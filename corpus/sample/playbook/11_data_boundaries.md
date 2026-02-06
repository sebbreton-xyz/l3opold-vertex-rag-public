---
id: pb.data.boundaries
version: 1.0.0
status: current
date: 2026-02-05
audience: mixed
---

# Data boundaries & sensitive content

Sensitive data can include personal identifiers or private records. Prefer data minimization.

Recommended boundaries:
- Document store: private documents (access-controlled).
- Vector index: embeddings + metadata; avoid storing sensitive text as metadata.
- Logs: avoid sensitive user input; store request IDs and minimal diagnostics.

Deletion & freshness:
When documents change:
- delete or invalidate related chunks
- re-index to reflect the current state
