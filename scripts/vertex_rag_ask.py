#!/usr/bin/env python3
"""
Query a Vertex RAG corpus with retrieve+generate, print sources WITH excerpts,
and save grounding metadata for audit.

Repro:
  source env.vertex.sh
  source .venv/bin/activate
  RUN_DIR="outputs/runs/$(date +%F)"
  CORPUS_NAME="$(cat $RUN_DIR/vertex_rag_corpus.txt)"

  python scripts/vertex_rag_ask.py \
    --corpus "$CORPUS_NAME" \
    --prompt "Define signal detection in pharmacovigilance..." \
    --top-k 8 \
    --distance-threshold 0.6 \
    --run-dir "$RUN_DIR"
"""

import argparse
import datetime as dt
import json
import os
import sys
import subprocess
import shlex
from typing import Any, Dict, List, Optional

import vertexai
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool

try:
    # For protobuf -> dict conversion (grounding metadata is often proto-backed)
    from google.protobuf.json_format import MessageToDict  # type: ignore
except Exception:
    MessageToDict = None  # type: ignore


def _pb_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Best-effort conversion of SDK/proto objects to dict for logging."""
    if obj is None:
        return None
    # Some SDK objects expose to_dict()
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            pass
    # Many Vertex SDK objects have a _pb attribute (protobuf message)
    pb = getattr(obj, "_pb", None)
    if pb is not None and MessageToDict is not None:
        try:
            return MessageToDict(pb, preserving_proto_field_name=True)
        except Exception:
            pass
    return None


def _gsutil_head(uri: str, max_chars: int = 500) -> Optional[str]:
    """
    Fallback: fetch a short excerpt from the GCS object itself.
    (Not necessarily the exact cited chunk, but useful for quick inspection.)
    """
    try:
        p = subprocess.run(
            ["gsutil", "cat", uri],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        txt = p.stdout.strip()
        if not txt:
            return None
        return txt[:max_chars]
    except Exception:
        return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, help="Full corpus resource name (projects/.../ragCorpora/...)")
    p.add_argument("--prompt", required=True)
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--distance-threshold", type=float, default=None,
                   help="Optional vector distance threshold filter (if supported).")
    p.add_argument("--model", default="gemini-2.0-flash-001")
    p.add_argument("--run-dir", default=None)
    p.add_argument("--excerpts", type=int, default=280, help="Chars to print per excerpt")
    args = p.parse_args()
    p.add_argument("--no-report-md", action="store_true", help="Disable writing report.md")


    project = os.environ.get("PROJECT_ID")
    location = os.environ.get("LOCATION") or os.environ.get("REGION")
    if not project or not location:
        print("ERROR: PROJECT_ID and (LOCATION or REGION) must be set in env.", file=sys.stderr)
        return 2

    run_dir = args.run_dir or f"outputs/runs/{dt.date.today().isoformat()}"
    os.makedirs(run_dir, exist_ok=True)

    vertexai.init(project=project, location=location)

    # Optional retrieval filter (distance threshold)
    retrieval_filter = None
    if args.distance_threshold is not None:
        try:
            retrieval_filter = rag.Filter(vector_distance_threshold=args.distance_threshold)
        except Exception:
            retrieval_filter = None  # SDK/version may not support it cleanly

    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[rag.RagResource(rag_corpus=args.corpus)],
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=args.top_k,
                    filter=retrieval_filter,
                ),
            )
        )
    )

    model = GenerativeModel(args.model, tools=[rag_tool])
    resp = model.generate_content(args.prompt)

    print("\n=== ANSWER ===\n")
    print(resp.text)

    # ---- Extract sources + excerpts from grounding metadata ----
    sources: List[Dict[str, Any]] = []
    grounding_dict: Optional[Dict[str, Any]] = None

    try:
        cand0 = resp.candidates[0]
        gm = getattr(cand0, "grounding_metadata", None)
        grounding_dict = _pb_to_dict(gm)

        grounding_chunks = getattr(gm, "grounding_chunks", None) or []
        for ch in grounding_chunks:
            rc = getattr(ch, "retrieved_context", None)
            uri = getattr(rc, "uri", None) if rc else None
            title = getattr(rc, "title", None) if rc else None

            # Prefer rag_chunk.text (more "exact" chunk) then fallback to rc.text
            snippet = None
            if rc:
                rag_chunk = getattr(rc, "rag_chunk", None)
                if rag_chunk:
                    snippet = getattr(rag_chunk, "text", None)

                if not snippet:
                    snippet = getattr(rc, "text", None)

            if snippet:
                snippet = snippet.strip()

            # Fallback if snippet still isn't available
            if (not snippet) and uri:
                snippet = _gsutil_head(uri, max_chars=max(500, args.excerpts * 2))


            if uri:
                sources.append({
                    "uri": uri,
                    "title": title,
                    "excerpt": (snippet[:args.excerpts] + "…") if snippet and len(snippet) > args.excerpts else snippet,
                })

    except Exception:
        pass

    # Deduplicate by URI (keep first)
    seen = set()
    dedup = []
    for s in sources:
        if s["uri"] in seen:
            continue
        seen.add(s["uri"])
        dedup.append(s)
    sources = dedup

    print("\n=== SOURCES (with excerpts) ===\n")
    for i, s in enumerate(sources, start=1):
        print(f"{i}. {s['uri']}")
        if s.get("title"):
            print(f"   title: {s['title']}")
        if s.get("excerpt"):
            print(f"   excerpt: {s['excerpt']}")
        else:
            print("   excerpt: (not available)")
        print()

    # ---- Save logs ----
    out_demo = os.path.join(run_dir, "vertex_rag_demo.json")
    with open(out_demo, "w", encoding="utf-8") as f:
        json.dump(
            {
                "project": project,
                "location": location,
                "corpus": args.corpus,
                "model": args.model,
                "top_k": args.top_k,
                "distance_threshold": args.distance_threshold,
                "prompt": args.prompt,
                "answer": resp.text,
                "sources": sources,
            },
            f,
            indent=2,
        )

    out_grounding = os.path.join(run_dir, "vertex_rag_grounding.json")
    with open(out_grounding, "w", encoding="utf-8") as f:
        json.dump(
            {
                "grounding_metadata": grounding_dict,
            },
            f,
            indent=2,
        )

    # ---- Audit: retrieved chunks (indexed) + citation mapping (if available) ----
    gm_dict = (grounding_dict or {})
    chunks = gm_dict.get("grounding_chunks", []) or []
    supports = gm_dict.get("grounding_supports", []) or []

    # Print indexed chunks (lets you see duplicates from same doc, and what was actually retrieved)
    if chunks:
        print("\n=== RETRIEVED CHUNKS (indexed) ===\n")
        for i, ch in enumerate(chunks):
            rc = (ch.get("retrieved_context") or {})
            uri = rc.get("uri")
            title = rc.get("title")

            # Prefer rag_chunk.text if present (more "exact" than rc.text)
            rag_chunk = rc.get("rag_chunk") or {}
            txt = (rag_chunk.get("text") or rc.get("text") or "").strip()

            ex = (txt[:args.excerpts] + "…") if txt and len(txt) > args.excerpts else txt
            print(f"[{i}] {uri}")
            if title:
                print(f"     title: {title}")
            print(f"     excerpt: {ex if ex else '(not available)'}\n")

    # Build segment->sources mapping if grounding_supports exist
    def _segment_text(s: dict, full_answer: str) -> Optional[str]:
        seg = s.get("segment") or {}
        if isinstance(seg, dict) and seg.get("text"):
            return str(seg["text"])
        start = seg.get("start_index")
        end = seg.get("end_index")
        if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(full_answer):
            return full_answer[start:end]
        return None

    def _chunk_uri(idx: int) -> Optional[str]:
        try:
            rc = chunks[idx].get("retrieved_context") or {}
            return rc.get("uri")
        except Exception:
            return None

    citations = []
    if supports:
        for s in supports:
            seg_txt = _segment_text(s, resp.text)
            idxs = s.get("grounding_chunk_indices") or []
            # normalize
            norm_idxs = []
            for x in idxs:
                try:
                    norm_idxs.append(int(x))
                except Exception:
                    pass
            uris = sorted({u for u in (_chunk_uri(i) for i in norm_idxs) if u})
            citations.append({
                "segment": seg_txt.strip() if isinstance(seg_txt, str) else None,
                "chunk_indices": norm_idxs,
                "uris": uris,
            })

        print("\n=== CITATION MAPPING (answer segment -> sources) ===\n")
        for i, c in enumerate(citations, start=1):
            seg = c["segment"] or "(segment text not available)"
            seg_short = (seg[:240] + "…") if len(seg) > 240 else seg
            print(f"{i}. {seg_short}")
            print(f"   chunks: {c['chunk_indices']}")
            for u in c["uris"]:
                print(f"   - {u}")
            print()

        out_citations = os.path.join(run_dir, "vertex_rag_citations.json")
        with open(out_citations, "w", encoding="utf-8") as f:
            json.dump({"citations": citations}, f, indent=2)
        print("Saved:", out_citations)
    else:
        print("\n(No grounding_supports found: cannot build exact segment->source mapping.)\n")

    print("Saved:", out_demo)
    print("Saved:", out_grounding)

        # ---- Repro command + inferred GCS prefix ----
    uris = [s.get("uri") for s in sources if s.get("uri")]
    gcs_prefix = None
    if uris:
        pref = os.path.commonprefix(uris)  # string common prefix
        if "/" in pref:
            gcs_prefix = pref[: pref.rfind("/") + 1]  # cut to last slash

    repro_parts = [
        "python", "scripts/vertex_rag_ask.py",
        "--corpus", args.corpus,
        "--prompt", args.prompt,
        "--top-k", str(args.top_k),
    ]
    if args.distance_threshold is not None:
        repro_parts += ["--distance-threshold", str(args.distance_threshold)]
    repro_parts += ["--run-dir", run_dir]

    # pretty multi-line bash command with proper quoting
    repro_cmd = " \\\n  ".join(shlex.quote(x) for x in repro_parts)


        # ---- Write Markdown report (optional) ----
    if not getattr(args, "no_report_md", False):

        report_path = os.path.join(run_dir, "report.md")
        run_ts = dt.datetime.now().isoformat(timespec="seconds")

        md = []
        md.append(f"# Vertex RAG run — {run_ts}\n")
        md.append("## Context\n")
        md.append(f"- Project: `{project}`\n")
        md.append(f"- Location: `{location}`\n")
        md.append(f"- Corpus: `{args.corpus}`\n")
        md.append(f"- Model: `{args.model}`\n")
        md.append(f"- Retrieval: `top_k={args.top_k}`\n")
        if args.distance_threshold is not None:
            md.append(f"- Filter: `vector_distance_threshold={args.distance_threshold}`\n")
        md.append("\n## Artifacts\n")
        md.append("\n## Repro command\n```bash\n")
        md.append("source env.vertex.sh\n")
        md.append("source .venv/bin/activate\n\n")
        md.append(repro_cmd + "\n")
        md.append("```\n")

        md.append("\n## GCS input prefix\n")
        if gcs_prefix:
            md.append(f"`{gcs_prefix}`\n")
        else:
            md.append("_Could not infer prefix from retrieved URIs._\n")

        md.append(f"- `vertex_rag_demo.json`\n")
        md.append(f"- `vertex_rag_grounding.json`\n")
        md.append(f"- `vertex_rag_citations.json` (if generated)\n")
        md.append("\n## Prompt\n")
        md.append("```text\n")
        md.append(args.prompt.strip() + "\n")
        md.append("```\n")
        md.append("\n## Answer\n")
        md.append(resp.text.strip() + "\n")

        md.append("\n## Sources (with excerpts)\n")
        if sources:
            for i, s in enumerate(sources, start=1):
                md.append(f"\n### {i}. {s.get('title') or ''}\n")
                md.append(f"- URI: `{s['uri']}`\n")
                ex = s.get("excerpt")
                if ex:
                    md.append("\n> " + "\n> ".join(ex.strip().splitlines()) + "\n")
        else:
            md.append("\n_No sources extracted._\n")

        # If your script builds `citations` (supports mapping), include it
        try:
            if citations:
                md.append("\n## Citation mapping (answer segment → sources)\n")
                for i, c in enumerate(citations, start=1):
                    seg = (c.get("segment") or "").strip()
                    if not seg:
                        seg = "(segment text not available)"
                    md.append(f"\n### {i}\n")
                    md.append(f"**Segment:** {seg}\n")
                    if c.get("chunk_indices") is not None:
                        md.append(f"- chunk_indices: `{c['chunk_indices']}`\n")
                    if c.get("uris"):
                        md.append("- URIs:\n")
                        for u in c["uris"]:
                            md.append(f"  - `{u}`\n")
            else:
                md.append("\n## Citation mapping\n_No grounding_supports / no mapping available._\n")
        except NameError:
            # citations variable not defined in this version
            md.append("\n## Citation mapping\n_Not enabled in this script version._\n")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(md))

        print("Saved:", report_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
