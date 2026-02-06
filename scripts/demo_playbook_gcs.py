from __future__ import annotations

import os
import shlex
import subprocess
from typing import List

from scripts.playbook_core import Doc, init_vertex, build_prompt, generate, pretty_print_json_or_raw


GOV_FILES = [
    "governance/identity_manifesto.md",
    "governance/output_format.md",
    "governance/rules_current.md",
    "governance/rules_obsolete.md",
    "governance/banned.txt",
    "governance/facts_tags.md",
]

PB_FILES = [
    "playbook/00_executive_overview.md",
    "playbook/01_user_guide.md",
    "playbook/02_privacy_security_faq.md",
    "playbook/10_architecture_overview.md",
    "playbook/11_data_boundaries.md",
    "playbook/12_indexing_chunking.md",
    "playbook/13_retrieval_embeddings.md",
    "playbook/14_citations_audit.md",
    "playbook/15_logging_policy_current.md",
    "playbook/90_logging_policy_obsolete.md",
]


def gcs_cat(uri: str) -> str:
    cmd = f"gsutil cat {shlex.quote(uri)}"
    return subprocess.check_output(cmd, shell=True, text=True)


def load_gcs_docs(bucket: str, prefix: str = "sample") -> List[Doc]:
    docs: List[Doc] = []
    for rel in GOV_FILES + PB_FILES:
        uri = f"gs://{bucket}/{prefix}/{rel}"
        docs.append(Doc(source=uri, text=gcs_cat(uri)))
    return docs


def main() -> None:
    init_vertex()

    bucket = os.environ["BUCKET"]
    prefix = os.environ.get("GCS_PREFIX", "sample")
    docs = load_gcs_docs(bucket, prefix)

    question = os.environ.get(
        "QUESTION",
        "Which policy is CURRENT regarding logging, and what is OBSOLETE?"
    )

    prompt = build_prompt(question, docs)
    output = generate(prompt)
    pretty_print_json_or_raw(output)


if __name__ == "__main__":
    main()
