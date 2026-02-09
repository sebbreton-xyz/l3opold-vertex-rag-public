#!/usr/bin/env python3
"""
Create a Vertex AI RAG corpus and import documents from a GCS prefix.

Repro:
  source env.vertex.sh
  source .venv/bin/activate
  python scripts/vertex_rag_create_import.py \
    --display-name pmc70-ew4 \
    --gcs-prefix "gs://$BUCKET/rag-input/pmc_txt/rag_input_docs/" \
    --run-dir "outputs/runs/$(date +%F)" \
    --chunk-size 512 \
    --chunk-overlap 100
"""

import argparse
import datetime as dt
import json
import os
import sys

import vertexai
from vertexai import rag


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--display-name", default=None, help="Corpus display name (default: pmc70-YYYY-MM-DD-ew4)")
    p.add_argument("--gcs-prefix", required=True, help="GCS prefix containing docs (e.g. gs://bucket/path/)")
    p.add_argument("--run-dir", default=None, help="Run directory (default: outputs/runs/YYYY-MM-DD)")
    p.add_argument("--chunk-size", type=int, default=512)
    p.add_argument("--chunk-overlap", type=int, default=100)
    p.add_argument("--embedding-model", default="publishers/google/models/text-embedding-005")
    p.add_argument("--rpm", type=int, default=1000, help="max_embedding_requests_per_min")
    args = p.parse_args()

    project = os.environ.get("PROJECT_ID")
    location = os.environ.get("LOCATION") or os.environ.get("REGION")
    bucket = os.environ.get("BUCKET")

    if not project or not location:
        print("ERROR: PROJECT_ID and (LOCATION or REGION) must be set in env.", file=sys.stderr)
        return 2

    today = dt.date.today().isoformat()
    run_dir = args.run_dir or f"outputs/runs/{today}"
    os.makedirs(run_dir, exist_ok=True)

    display_name = args.display_name or f"pmc70-{today}-{location}"

    vertexai.init(project=project, location=location)

    embedding_model_config = rag.RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model=args.embedding_model
        )
    )

    rag_corpus = rag.create_corpus(
        display_name=display_name,
        backend_config=rag.RagVectorDbConfig(
            rag_embedding_model_config=embedding_model_config
        ),
    )

    rag.import_files(
        rag_corpus.name,
        [args.gcs_prefix],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            )
        ),
        max_embedding_requests_per_min=args.rpm,
    )

    corpus_txt = os.path.join(run_dir, "vertex_rag_corpus.txt")
    with open(corpus_txt, "w", encoding="utf-8") as f:
        f.write(rag_corpus.name + "\n")

    meta_json = os.path.join(run_dir, "vertex_rag_import_meta.json")
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "project": project,
                "location": location,
                "bucket_env": bucket,
                "gcs_prefix": args.gcs_prefix,
                "display_name": display_name,
                "corpus_name": rag_corpus.name,
                "chunk_size": args.chunk_size,
                "chunk_overlap": args.chunk_overlap,
                "embedding_model": args.embedding_model,
                "rpm": args.rpm,
            },
            f,
            indent=2,
        )

    print("✅ CORPUS:", rag_corpus.name)
    print("Saved:", corpus_txt)
    print("Saved:", meta_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
