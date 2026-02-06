from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import vertexai
from vertexai.generative_models import GenerativeModel


@dataclass(frozen=True)
class Doc:
    source: str  # file path or URI
    text: str


def init_vertex() -> None:
    project_id = os.environ["PROJECT_ID"]
    region = os.environ.get("REGION", "europe-west1")
    vertexai.init(project=project_id, location=region)


def load_local_docs(base_dir: Path) -> List[Doc]:
    """Load all docs under corpus/sample/(governance|playbook) in a stable order."""
    gov = base_dir / "governance"
    pb = base_dir / "playbook"

    paths: List[Path] = []
    if gov.exists():
        paths += sorted(gov.glob("*.*"))
    if pb.exists():
        paths += sorted(pb.glob("*.*"))

    docs: List[Doc] = []
    for p in paths:
        docs.append(Doc(source=str(p), text=p.read_text(encoding="utf-8")))
    return docs

def build_prompt(question: str, docs: Iterable[Doc]) -> str:
    """Create a grounding prompt: rules + doc-only + strict JSON output."""
    docs_list = list(docs)

    allowed_sources = "\n".join(f"- {d.source}" for d in docs_list)
    context = "\n\n---\n\n".join(d.text for d in docs_list)

    return f"""
You are a demonstration assistant for a private RAG playbook.

STRICT REQUIREMENTS:
- Use ONLY the provided documents.
- Prefer rules marked status: current over status: obsolete when they contradict.
- Output MUST be valid JSON matching the required schema from governance/output_format.md.
- Do NOT use any banned words listed in governance/banned.txt.
- If something is not found in the documents, say so explicitly (do not guess).
- In "sources", list at least 2 sources you actually used.
- "sources" MUST be chosen EXACTLY from the list under ALLOWED_SOURCES. Do not invent IDs.

ALLOWED_SOURCES:
{allowed_sources}

QUESTION:
{question}

DOCUMENTS (for grounding):
{context}
""".strip()



def generate(prompt: str) -> str:
    model_name = os.environ.get("MODEL", "gemini-2.0-flash-001")
    model = GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()


def pretty_print_json_or_raw(text: str) -> None:
    try:
        data = json.loads(text)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(text)
