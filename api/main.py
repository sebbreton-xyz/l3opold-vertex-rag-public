import datetime as dt
import json
import os
import re
import subprocess
import time
import uuid
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import vertexai
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool

try:
    from google.protobuf.json_format import MessageToDict  # type: ignore
except Exception:
    MessageToDict = None  # type: ignore


# -----------------------------
# Helpers (PMC + redaction)
# -----------------------------
_PMC_RE = re.compile(r"pmc[_-]?(\d+)", re.IGNORECASE)


def _pmc_id_from_title_or_uri(
    title: Optional[str], uri: Optional[str]
) -> Optional[str]:
    for s in (title, uri):
        if not s:
            continue
        m = _PMC_RE.search(s)
        if m:
            return m.group(1)
    return None


def _pmc_url(pmc_digits: str) -> str:
    return f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_digits}/"


def _dedup_by_key(items: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        v = it.get(key)
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(it)
    return out


def _pb_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
    if obj is None:
        return None
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            pass
    pb = getattr(obj, "_pb", None)
    if pb is not None and MessageToDict is not None:
        try:
            return MessageToDict(pb, preserving_proto_field_name=True)
        except Exception:
            pass
    return None


def _gsutil_head(uri: str, max_chars: int = 600) -> Optional[str]:
    """Read first bytes of a gs:// object (used only to build an excerpt)."""
    try:
        p = subprocess.run(
            ["gsutil", "cat", uri],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        txt = p.stdout.strip()
        return txt[:max_chars] if txt else None
    except Exception:
        return None


# -----------------------------
# Config
# -----------------------------
PUBLIC_MODE = os.environ.get("PUBLIC_MODE", "0") == "1"
# Default: redact gs:// in API responses (good for public repos)
REDACT_GCS_URIS = os.environ.get("REDACT_GCS_URIS", "1") == "1"

PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION") or os.environ.get("REGION")
DEFAULT_CORPUS = os.environ.get("VERTEX_RAG_CORPUS")
RUNS_DIR = os.environ.get("RUNS_DIR", "outputs/runs")
API_TOKEN = os.environ.get("API_TOKEN")  # optional bearer auth

TOP_K_MAX = int(os.environ.get("TOP_K_MAX", "10"))
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "512"))

# Runs base (absolute, stable)
RUNS_BASE = Path(RUNS_DIR)
if not RUNS_BASE.is_absolute():
    RUNS_BASE = (Path.cwd() / RUNS_BASE).resolve()

DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RUN_ID_RE = re.compile(r"^[0-9a-f]{8,32}$")  # your ids are 12 hex; allow wider

ARTIFACTS = {
    "report": ("report.md", "text/markdown; charset=utf-8"),
    "demo": ("vertex_rag_demo.json", "application/json"),
    "grounding": ("vertex_rag_grounding.json", "application/json"),
    "citations": ("vertex_rag_citations.json", "application/json"),
}


def _require_env() -> None:
    if not PROJECT_ID or not LOCATION:
        raise RuntimeError("PROJECT_ID and (LOCATION or REGION) must be set.")

    # IMPORTANT:
    # - Rédaction (REDACT_GCS_URIS / PUBLIC_MODE) = content
    # - API_TOKEN = access control
    # We don’t force the token just to hide URIs
    if PUBLIC_MODE and not API_TOKEN:
        print(
            "WARNING: PUBLIC_MODE=1 but API_TOKEN is not set. "
            "This is OK for local use, but if you deploy publicly, set API_TOKEN to protect /ask and /runs.",
            file=sys.stderr,
        )


def _check_auth(authorization: Optional[str]) -> None:
    """If API_TOKEN is set, require Authorization: Bearer <token>."""
    if not API_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


def _validate_day(day: str) -> str:
    if not DAY_RE.match(day):
        raise HTTPException(
            status_code=400, detail="Invalid day format (expected YYYY-MM-DD)"
        )
    return day


def _validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id")
    return run_id


def _run_dir_path(day: str, run_id: str) -> Path:
    """Resolve run directory safely under RUNS_BASE/day/run_id."""
    day = _validate_day(day)
    run_id = _validate_run_id(run_id)

    p = (RUNS_BASE / day / run_id).resolve()
    if RUNS_BASE not in p.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    return p


def _artifact_path(day: str, run_id: str, kind: str) -> Path:
    if kind not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="Unknown artifact kind")
    run_dir = _run_dir_path(day, run_id)
    filename, _mt = ARTIFACTS[kind]
    p = (run_dir / filename).resolve()
    if run_dir not in p.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    return p


def _links(day: str, run_id: str) -> Dict[str, str]:
    base = f"/runs/{day}/{run_id}"
    return {
        "run": base,
        "report": f"{base}/report",
        "demo": f"{base}/demo",
        "grounding": f"{base}/grounding",
        "citations": f"{base}/citations",
    }


# -----------------------------
# API models
# -----------------------------
class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    top_k: int = Field(8, ge=1)
    distance_threshold: Optional[float] = Field(0.6, ge=0.0, le=2.0)
    model: str = Field("gemini-2.0-flash-001")
    corpus: Optional[str] = Field(
        None,
        description="Vertex ragCorpora full name. Defaults to env VERTEX_RAG_CORPUS.",
    )
    save_report: bool = Field(True, description="Write report.md in run dir")
    excerpts: int = Field(280, ge=60, le=2000)


class AskResponse(BaseModel):
    request_id: str
    run_dir: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieved_chunks: int
    retrieved_docs: int
    latency_ms: int
    guardrails: Dict[str, Any]
    links: Dict[str, str]


# -----------------------------
# App + static UI
# -----------------------------
app = FastAPI(title="L3opold Vertex RAG API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.head("/")
def root_head():
    # Helps `curl -I /` avoid a 405 in some setups
    return {}


@app.on_event("startup")
def _startup() -> None:
    _require_env()
    vertexai.init(project=PROJECT_ID, location=LOCATION)


@app.get("/healthz")
def healthz():
    return {"ok": True, "project": PROJECT_ID, "location": LOCATION}


# -----------------------------
# Runs browsing / artifact serving
# -----------------------------
@app.get("/runs/{day}")
def list_runs(day: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)

    day = _validate_day(day)
    day_dir = (RUNS_BASE / day).resolve()

    if RUNS_BASE not in day_dir.parents:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not day_dir.exists() or not day_dir.is_dir():
        return {"day": day, "runs": [], "count": 0}

    runs: List[str] = []
    for p in sorted(day_dir.iterdir()):
        if p.is_dir() and RUN_ID_RE.match(p.name):
            runs.append(p.name)

    return {"day": day, "runs": runs, "count": len(runs)}


@app.get("/runs/{day}/{run_id}")
def get_run(day: str, run_id: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    run_dir = _run_dir_path(day, run_id)

    present = {}
    for kind, (fname, _mt) in ARTIFACTS.items():
        present[kind] = (run_dir / fname).exists()

    return {
        "day": day,
        "run_id": run_id,
        "run_dir": str(Path(RUNS_DIR) / day / run_id),
        "artifacts_present": present,
        "links": _links(day, run_id),
    }


@app.get("/runs/{day}/{run_id}/{kind}")
def get_artifact(
    day: str,
    run_id: str,
    kind: str,
    download: bool = Query(False, description="If true, force download"),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    p = _artifact_path(day, run_id, kind)
    _fname, mt = ARTIFACTS[kind]

    headers: Dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{p.name}"'

    return FileResponse(str(p), media_type=mt, headers=headers)


# -----------------------------
# Main endpoint
# -----------------------------
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)

    corpus = req.corpus or DEFAULT_CORPUS
    if not corpus:
        raise HTTPException(
            status_code=400,
            detail="Missing corpus. Set env VERTEX_RAG_CORPUS or pass corpus in request.",
        )
    if req.top_k > TOP_K_MAX:
        raise HTTPException(
            status_code=400, detail=f"top_k too high (max {TOP_K_MAX})."
        )

    # Run dir for audit artifacts
    request_id = uuid.uuid4().hex[:12]
    day = dt.date.today().isoformat()
    run_dir_fs = RUNS_BASE / day / request_id
    run_dir_fs.mkdir(parents=True, exist_ok=True)

    # For API response (relative, nicer)
    run_dir = str(Path(RUNS_DIR) / day / request_id)

    # Metrics (latency + retrieval counts)
    t0 = time.perf_counter()
    retrieved_chunks = 0

    # Optional retrieval filter
    retrieval_filter = None
    if req.distance_threshold is not None:
        try:
            retrieval_filter = rag.Filter(
                vector_distance_threshold=req.distance_threshold
            )
        except Exception:
            retrieval_filter = None

    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[rag.RagResource(rag_corpus=corpus)],
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=req.top_k,
                    filter=retrieval_filter,
                ),
            )
        )
    )

    try:
        model = GenerativeModel(
            req.model,
            tools=[rag_tool],
            generation_config={"max_output_tokens": MAX_OUTPUT_TOKENS},
        )
        resp = model.generate_content(req.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Vertex call failed: {str(e)[:1800]}"
        )

    # Grounding extraction
    sources: List[Dict[str, Any]] = []
    grounding_dict: Optional[Dict[str, Any]] = None

    try:
        cand0 = resp.candidates[0]
        gm = getattr(cand0, "grounding_metadata", None)
        grounding_dict = _pb_to_dict(gm)

        grounding_chunks = getattr(gm, "grounding_chunks", None) or []
        retrieved_chunks = len(grounding_chunks)

        for ch in grounding_chunks:
            rc = getattr(ch, "retrieved_context", None)
            uri = getattr(rc, "uri", None) if rc else None
            title = getattr(rc, "title", None) if rc else None

            snippet = getattr(rc, "text", None) if rc else None
            if snippet:
                snippet = snippet.strip()

            # If rc.text isn't present, fetch small excerpt from GCS (still does NOT expose gs:// in response)
            if (not snippet) and uri:
                snippet = _gsutil_head(uri, max_chars=max(800, req.excerpts * 2))

            if not uri:
                continue

            pmc_digits = _pmc_id_from_title_or_uri(title, uri)
            source_id = f"pmc_{pmc_digits}" if pmc_digits else (title or "source")

            item: Dict[str, Any] = {
                "id": source_id,
                "title": title,
                "excerpt": (
                    (snippet[: req.excerpts] + "…")
                    if snippet and len(snippet) > req.excerpts
                    else snippet
                ),
            }

            # Public PMC link (preferred)
            if pmc_digits:
                item["pmc_url"] = _pmc_url(pmc_digits)

            # Raw gs:// only if explicitly allowed
            if not (PUBLIC_MODE or REDACT_GCS_URIS):
                item["uri"] = uri

            sources.append(item)

    except Exception:
        # Keep API resilient: return answer even if grounding extraction fails
        pass

        sources = _dedup_by_key(sources, "id")

    retrieved_docs = len(sources)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    guardrails = {"top_k_max": TOP_K_MAX, "max_output_tokens": MAX_OUTPUT_TOKENS}
    links = _links(day, request_id)

    # Save artifacts (demo + grounding + report)
    out_demo = run_dir_fs / "vertex_rag_demo.json"
    out_demo.write_text(
        json.dumps(
            {
                "request_id": request_id,
                "project": PROJECT_ID,
                "location": LOCATION,
                "corpus": corpus,
                "model": req.model,
                "top_k": req.top_k,
                "distance_threshold": req.distance_threshold,
                "prompt": req.prompt,
                "answer": resp.text,
                "sources": sources,
                "latency_ms": latency_ms,
                "retrieved_chunks": retrieved_chunks,
                "retrieved_docs": retrieved_docs,
                "guardrails": guardrails,
                "links": links,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    out_grounding = run_dir_fs / "vertex_rag_grounding.json"
    out_grounding.write_text(
        json.dumps({"grounding_metadata": grounding_dict}, indent=2),
        encoding="utf-8",
    )

    if req.save_report:
        report = run_dir_fs / "report.md"
        with report.open("w", encoding="utf-8") as f:
            f.write(
                f"# Vertex RAG API run — {dt.datetime.now().isoformat(timespec='seconds')}\n"
            )
            f.write("## Context\n")
            f.write(f"- Project: `{PROJECT_ID}`\n")
            f.write(f"- Location: `{LOCATION}`\n")
            f.write(f"- Corpus: `{corpus}`\n")
            f.write(f"- Model: `{req.model}`\n")
            f.write(f"- Retrieval: `top_k={req.top_k}`\n")
            f.write(f"- Filter: `vector_distance_threshold={req.distance_threshold}`\n")
            f.write(f"- Request: `{request_id}`\n")
            f.write(f"- Latency: `{latency_ms}ms`\n")
            f.write(
                f"- Retrieved: `chunks={retrieved_chunks}`, `docs={retrieved_docs}`\n"
            )
            f.write(
                f"- Guardrails: `top_k_max={TOP_K_MAX}`, `max_output_tokens={MAX_OUTPUT_TOKENS}`\n\n"
            )

            f.write("## Links\n")
            f.write(f"- report: `{links['report']}`\n")
            f.write(f"- demo: `{links['demo']}`\n")
            f.write(f"- grounding: `{links['grounding']}`\n")
            f.write(f"- citations: `{links['citations']}`\n\n")

            f.write("## Prompt\n```text\n" + req.prompt + "\n```\n\n")
            f.write("## Answer\n" + (resp.text or "") + "\n\n")

            f.write("## Sources (with excerpts)\n\n")
            for i, s in enumerate(sources, 1):
                f.write(f"### {i}. {s.get('title') or s.get('id') or 'source'}\n")
                if s.get("pmc_url"):
                    f.write(f"- PMC: `{s['pmc_url']}`\n")
                if s.get("uri"):
                    f.write(f"- URI: `{s['uri']}`\n")
                if s.get("id"):
                    f.write(f"- ID: `{s['id']}`\n")
                f.write("\n")

                ex = s.get("excerpt") or "(not available)"
                f.write("> " + "\n> ".join(str(ex).splitlines()) + "\n\n")

    return AskResponse(
        request_id=request_id,
        run_dir=run_dir,
        answer=resp.text or "",
        sources=sources,
        retrieved_chunks=retrieved_chunks,
        retrieved_docs=retrieved_docs,
        latency_ms=latency_ms,
        guardrails=guardrails,
        links=links,
    )
