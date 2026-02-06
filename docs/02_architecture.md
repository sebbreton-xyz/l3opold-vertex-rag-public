```text
[Terminal]  python3 -m scripts.demo_playbook_local
    |
    v
[demo_playbook_local.py]
    |
    |--(1) init_vertex()
    |        |
    |        +--> vertexai.init(project=PROJECT_ID, location=REGION)
    |
    |--(2) load_local_docs("corpus/sample")
    |        |
    |        +--> reads the. md/. txt (governance + playbook)
    |        +--> create a Doc list (source=path, text=content)
    |
    |--(3) question = $QUESTION (otherwise question by default)
    |
    |--(4) build_prompt(question, docs)
    |        |
    |        +--> make a PROMPT text that contains :
    |              - strict rules (JSON, current>obsolete, banned)
    |              - ALLOWED_SOURCES (exact list of paths)
    |              - DOCUMENTS (all the concatenated content)
    |
    |--(5) generate(prompt)
    |        |
    |        +--> Vertex AI (Gemini) via GenerativeModel.generate_content(prompt)
    |
    |--(6) pretty_print_json_or_raw(resp.text)
             |
             +--> displays the JSON (indented)
```