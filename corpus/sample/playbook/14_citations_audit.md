---
id: pb.citations.audit
version: 1.0.0
status: current
date: 2026-02-05
audience: mixed
---

# Citations & audit trail

Citations allow verification: users can trace claims back to sources.

Store per answer:
- query
- retrieved chunk IDs + scores
- sources used
- model parameters (top-k, temperature)

Guardrail:
If a claim has no supporting chunk, do not state it as a fact.
