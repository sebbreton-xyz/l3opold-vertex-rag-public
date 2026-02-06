---
id: pb.logging.policy
version: 1.0.0
status: current
date: 2026-02-05
audience: mixed
---

# Logging policy (CURRENT)

Logs are for reliability and auditing, not for collecting sensitive content.

Rules:
- Do NOT log full user queries if they may contain sensitive data.
- Do NOT log private document excerpts.
- Prefer request IDs and minimal diagnostics.
- Short retention by default; extend only with explicit approval and restricted access.
