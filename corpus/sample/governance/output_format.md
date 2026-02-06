---
id: sample.format
version: 1.0.0
status: current
date: 2026-02-05
---

# Required output format

Output MUST be valid JSON with exactly these keys:

{
  "corpus_id": "string",
  "tags": ["string", "string", "string"],
  "answer": "string",
  "sources": ["string", "string"],
  "final_line": "string"
}

Constraints:
- Language: EN
- answer length: 80–120 words
- tags: exactly 3 tags (see facts_tags)
- sources: file paths actually used
- final_line: exact phrase (see facts_tags)
