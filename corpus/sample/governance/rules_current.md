---
id: sample.rules
version: 2.0.0
status: current
date: 2026-02-05
priority: 100
---

# CURRENT rules

1) Version precedence
- If documents contradict each other, prefer status: current and ignore status: obsolete.

2) Grounding / Doc-only behavior
- Answer using the provided documents only.
- If a detail is not present in the documents, say so explicitly.

3) Sources
- "sources" must list the documents actually used (prefer at least 2).

4) Forbidden terms
- Do not use any word listed in banned.txt (case-insensitive).
