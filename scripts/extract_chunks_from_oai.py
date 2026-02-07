import glob, os, re, json
from xml.etree import ElementTree as ET

IN_DIR = "data/raw/pmc_xml"
OUT_PATH = "artifacts/chunks.jsonl"

MAX_CHARS = 1200   # chunk size (chars)
OVERLAP = 150      # overlap (chars)

def normalize_ws(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s

def iter_text(elem):
    # Collect all text content from an element subtree
    parts = []
    for t in elem.itertext():
        t = normalize_ws(t)
        if t:
            parts.append(t)
    return normalize_ws(" ".join(parts))

def chunk_text(text: str, max_chars=MAX_CHARS, overlap=OVERLAP):
    text = normalize_ws(text)
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks

def extract_oai_article(root: ET.Element):
    # OAI-PMH -> GetRecord -> record -> metadata -> article
    ns = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
    }
    md = root.find(".//{http://www.openarchives.org/OAI/2.0/}metadata")
    if md is None:
        return None
    # article may be nested with different namespaces; find first tag ending with 'article'
    for el in md.iter():
        if el.tag.endswith("article"):
            return el
    return None

def find_first_text(article, tag_suffix):
    for el in article.iter():
        if el.tag.endswith(tag_suffix):
            txt = iter_text(el)
            if txt:
                return txt
    return ""

def main():
    files = sorted(glob.glob(os.path.join(IN_DIR, "*.xml")))
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    out = open(OUT_PATH, "w", encoding="utf-8")
    total_docs = 0
    total_chunks = 0

    for path in files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception:
            continue

        # quick skip: avoid HTML / non-XML payloads
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(2000)
            if "<!doctype html" in head.lower() or "too many requests" in head.lower():
                continue
        except Exception:
            pass

        article = extract_oai_article(root)
        if article is None:
            continue

        doc_id = os.path.basename(path).replace("PMC", "").replace(".xml", "")
        title = find_first_text(article, "article-title")
        abstract = find_first_text(article, "abstract")

        # Build a rough "body" by taking all <sec> text blocks (keeps some structure)
        sections = []
        for el in article.iter():
            if el.tag.endswith("sec"):
                sec_txt = iter_text(el)
                if sec_txt and len(sec_txt) > 200:
                    sections.append(sec_txt)

        # Fallback: whole article text if sections empty
        body = " ".join(sections) if sections else iter_text(article)

        payloads = []
        if title:
            payloads.append(("title", title))
        if abstract:
            payloads.append(("abstract", abstract))
        if body:
            payloads.append(("body", body))

        doc_chunk_idx = 0
        for section_name, text in payloads:
            for ch in chunk_text(text):
                rec = {
                    "doc_id": doc_id,
                    "source": path,
                    "section": section_name,
                    "chunk_id": f"{doc_id}:{section_name}:{doc_chunk_idx}",
                    "text": ch,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                doc_chunk_idx += 1
                total_chunks += 1

        total_docs += 1

    out.close()
    print(f"Docs processed: {total_docs}")
    print(f"Chunks written: {total_chunks}")
    print(f"Output: {OUT_PATH}")

if __name__ == "__main__":
    main()
