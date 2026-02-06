from __future__ import annotations

import os
from pathlib import Path

from scripts.playbook_core import init_vertex, load_local_docs, build_prompt, generate, pretty_print_json_or_raw


def main() -> None:
    init_vertex()

    base_dir = Path("corpus/sample")
    docs = load_local_docs(base_dir)

    question = os.environ.get(
        "QUESTION",
        "What is the CURRENT logging policy, and what should NOT be logged?"
    )

    prompt = build_prompt(question, docs)
    output = generate(prompt)
    pretty_print_json_or_raw(output)


if __name__ == "__main__":
    main()
