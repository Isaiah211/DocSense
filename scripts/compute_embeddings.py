import json
import argparse
from pathlib import Path
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", default="data/index/metadata.json", help="Path to chunk metadata JSON")
    parser.add_argument("--out-emb", default="data/index/embeddings.npy", help="Output embeddings .npy file")
    parser.add_argument("--out-meta", default="data/index/embeddings_meta.json", help="Output embeddings meta JSON")
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError("sentence-transformers is required. Install it before running this script.") from e

    meta_path = Path(args.meta)
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    texts = [d.get("text", "") for d in data]
    chunk_ids = [d.get("chunk_id") for d in data]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    out_emb = Path(args.out_emb)
    out_emb.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(out_emb), embeddings)

    emb_meta = [{"chunk_id": cid, "file": d.get("file"), "index": i} for i, (cid, d) in enumerate(zip(chunk_ids, data))]
    out_meta = Path(args.out_meta)
    out_meta.write_text(json.dumps(emb_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote embeddings {embeddings.shape} to {out_emb}")
    print(f"Wrote embeddings meta to {out_meta}")


if __name__ == "__main__":
    main()
