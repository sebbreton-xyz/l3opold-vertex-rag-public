---
id: pb.arch.overview
version: 1.0.0
status: current
date: 2026-02-05
audience: mixed
---

# Architecture overview (private RAG)

## Core idea
The system stores private documents, retrieves the most relevant excerpts, and generates an answer grounded in those excerpts.
The answer includes sources so humans can verify what was used.

## Main components
1) Document store: private location for original documents (e.g., object storage).
2) Indexing pipeline: converts documents into chunks + metadata.
3) Vector index: stores embeddings for chunks to enable semantic search.
4) Retriever: selects top-k chunks for a query.
5) Generator: produces the final answer using retrieved chunks + strict rules.

## Key properties
- “Doc-only” behavior: no guessing if information is missing.
- Version precedence: current policies override obsolete ones.
- Auditability: store which chunks were used to produce the answer.
