import datetime as dt
import json
import os
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

import vertexai
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool

try:
    from google.protobuf.json_format import MessageToDict  # type: ignore
except Exception:
    MessageToDict = None  # type: ignore


# -----------------------------
# Config
# -----------------------------
PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION") or os.environ.get("REGION")
DEFAULT_CORPUS = os.environ.get("VERTEX_RAG_CORPUS")  # set it in env (local)
RUNS_DIR = os.environ.get("RUNS_DIR", "outputs/runs")
API_TOKEN = os.environ.get("API_TOKEN")  # optional: simple bearer auth

TOP_K_MAX = int(os.environ.get("TOP_K_MAX", "10"))
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "512"))


def _require_env():
    if not PROJECT_ID or not LOCATION:
        raise RuntimeError("PROJECT_ID and (LOCATION or REGION) must be set.")


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


def _dedup_by_uri(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        u = it.get("uri")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(it)
    return out


# -----------------------------
# API models
# -----------------------------
class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    top_k: int = Field(8, ge=1)
    distance_threshold: Optional[float] = Field(0.6, ge=0.0, le=2.0)
    model: str = Field("gemini-2.0-flash-001")
    corpus: Optional[str] = Field(None, description="Vertex ragCorpora full name. Defaults to env VERTEX_RAG_CORPUS.")
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


app = FastAPI(title="L3opold Vertex RAG API", version="0.1.0")


@app.on_event("startup")
def _startup():
    _require_env()
    vertexai.init(project=PROJECT_ID, location=LOCATION)


@app.get("/healthz")
def healthz():
    return {"ok": True, "project": PROJECT_ID, "location": LOCATION}


def _check_auth(authorization: Optional[str]):
    if not API_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


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
        raise HTTPException(status_code=400, detail=f"top_k too high (max {TOP_K_MAX}).")

    # Run dir for audit artifacts
    request_id = uuid.uuid4().hex[:12]
    day = dt.date.today().isoformat()
    run_dir = os.path.join(RUNS_DIR, day, request_id)
    os.makedirs(run_dir, exist_ok=True)

    # Metrics (latency + retrieval counts)
    t0 = time.perf_counter()
    retrieved_chunks = 0

    # Optional retrieval filter
    retrieval_filter = None
    if req.distance_threshold is not None:
        try:
            retrieval_filter = rag.Filter(vector_distance_threshold=req.distance_threshold)
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

    model = GenerativeModel(
        req.model,
        tools=[rag_tool],
        generation_config={"max_output_tokens": MAX_OUTPUT_TOKENS},
    )
    resp = model.generate_content(req.prompt)

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
            if (not snippet) and uri:
                snippet = _gsutil_head(uri, max_chars=max(800, req.excerpts * 2))

            if uri:
                sources.append(
                    {
                        "uri": uri,
                        "title": title,
                        "excerpt": (snippet[: req.excerpts] + "…") if snippet and len(snippet) > req.excerpts else snippet,
                    }
                )
    except Exception:
        # keep API resilient: return answer even if grounding extraction fails
        pass

    sources = _dedup_by_uri(sources)

    retrieved_docs = len(sources)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    guardrails = {"top_k_max": TOP_K_MAX, "max_output_tokens": MAX_OUTPUT_TOKENS}

    # Save artifacts (demo + grounding + report)
    out_demo = os.path.join(run_dir, "vertex_rag_demo.json")
    with open(out_demo, "w", encoding="utf-8") as f:
        json.dump(
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
            },
            f,
            indent=2,
        )

    out_grounding = os.path.join(run_dir, "vertex_rag_grounding.json")
    with open(out_grounding, "w", encoding="utf-8") as f:
        json.dump({"grounding_metadata": grounding_dict}, f, indent=2)

    if req.save_report:
        report = os.path.join(run_dir, "report.md")
        with open(report, "w", encoding="utf-8") as f:
            f.write(f"# Vertex RAG API run — {dt.datetime.now().isoformat(timespec='seconds')}\n")
            f.write("## Context\n")
            f.write(f"- Project: `{PROJECT_ID}`\n")
            f.write(f"- Location: `{LOCATION}`\n")
            f.write(f"- Corpus: `{corpus}`\n")
            f.write(f"- Model: `{req.model}`\n")
            f.write(f"- Retrieval: `top_k={req.top_k}`\n")
            f.write(f"- Filter: `vector_distance_threshold={req.distance_threshold}`\n")
            f.write(f"- Request: `{request_id}`\n")
            f.write(f"- Latency: `{latency_ms}ms`\n")
            f.write(f"- Retrieved: `chunks={retrieved_chunks}`, `docs={retrieved_docs}`\n")
            f.write(f"- Guardrails: `top_k_max={TOP_K_MAX}`, `max_output_tokens={MAX_OUTPUT_TOKENS}`\n\n")

            f.write("## Prompt\n```text\n" + req.prompt + "\n```\n\n")
            f.write("## Answer\n" + (resp.text or "") + "\n\n")
            f.write("## Sources (with excerpts)\n\n")
            for i, s in enumerate(sources, 1):
                f.write(f"### {i}. {s.get('title') or 'source'}\n")
                f.write(f"- URI: `{s['uri']}`\n\n")
                ex = s.get("excerpt") or "(not available)"
                f.write("> " + "\n> ".join(ex.splitlines()) + "\n\n")

    return AskResponse(
        request_id=request_id,
        run_dir=run_dir,
        answer=resp.text or "",
        sources=sources,
        retrieved_chunks=retrieved_chunks,
        retrieved_docs=retrieved_docs,
        latency_ms=latency_ms,
        guardrails=guardrails,
    )
