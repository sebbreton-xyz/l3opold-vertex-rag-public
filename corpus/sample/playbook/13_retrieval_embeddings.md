---
id: pb.retrieval.embeddings
version: 1.0.0
status: current
date: 2026-02-05
audience: technical
---

# Retrieval & embeddings (semantic search)

Keyword search matches exact terms and fails on paraphrases.
Embeddings represent meaning and can retrieve relevant text even when wording differs.

Top-k:
Retrieve the best k chunks and pass them to the generator.
If retrieval is empty/irrelevant, the assistant must say “not found in the documents”.
