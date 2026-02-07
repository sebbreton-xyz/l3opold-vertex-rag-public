# Lab Notebook

Chronological record of runs and validation steps (POC).

## 2026-02-07

- **Chunk extraction (OA PMC XML → JSONL)**  
  Command: `python scripts/extract_chunks_from_oai.py`  
  Output: `artifacts/chunks.jsonl` (**4,417** lines; `wc -l`)  
  Sanity check: `head -n 2 artifacts/chunks.jsonl` confirms expected fields (`doc_id`, `source`, `section`, `chunk_id`, `text`).
  
- **Pre-embeddings QC (chunks)** — integrity + sampling checks before embeddings/indexing.  
  → See: `runbook/2026-02-07_pre-embeddings-qc.md`
