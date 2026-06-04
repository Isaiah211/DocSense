from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path

app = FastAPI(title="DocSense API")


class Query(BaseModel):
    q: str


@app.on_event("startup")
def load_index():
    # Minimal prototype: load metadata only
    global METADATA
    metadata_path = Path("data/index/metadata.json")
    if metadata_path.exists():
        METADATA = json.loads(metadata_path.read_text(encoding="utf-8"))
    else:
        METADATA = []


@app.post("/search")
def search(query: Query):
    # In prototype, return top textual matches by simple substring match
    q = query.q.lower()
    results = []
    for item in METADATA:
        if q in item.get("text", "").lower():
            results.append({"file": item["file"], "chunk_id": item["chunk_id"], "text": item["text"]})
            if len(results) >= 10:
                break
    return {"query": q, "matches": results}
