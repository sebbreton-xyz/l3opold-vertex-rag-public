---
id: pb.indexing.chunking
version: 1.0.0
status: current
date: 2026-02-05
audience: technical
---

# Indexing & chunking

Chunking splits documents into retrievable excerpts.

Guidelines:
- Use headings / paragraphs as boundaries.
- Target: 250–450 tokens per chunk.
- Overlap: 30–60 tokens.

Minimal metadata:
- source_path, doc_id, status, version, chunk_id

Keep indexing deterministic for reproducibility.
