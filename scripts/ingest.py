import os
import json
import argparse
from pathlib import Path

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if start >= length:
            break
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="data/docs", help="Directory with documents")
    parser.add_argument("--index-path", default="data/index", help="Output index folder")
    args = parser.parse_args()

    doc_dir = Path(args.dir)
    out_dir = Path(args.index_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    documents = []
    for p in doc_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".txt":
            text = p.read_text(encoding="utf-8", errors="ignore")
            chunks = chunk_text(text)
            for i, c in enumerate(chunks):
                documents.append({
                    "file": str(p),
                    "chunk_id": f"{p.name}::chunk::{i}",
                    "text": c,
                })

    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(documents)} chunks to {meta_path}")


if __name__ == "__main__":
    main()
