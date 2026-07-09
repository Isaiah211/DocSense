"""
app/ingest.py
-------------
Reusable document ingestion helpers used by the FastAPI document endpoints.

The chunking and embedding logic is adapted from the top-level Chunk.py
script so it can be called in-process by the API (no subprocess needed).
After ingestion the LRU search-index caches in semantic_search_utils are
cleared so the next RAG query picks up the new embeddings automatically.
"""

import json
import os
import re
from typing import Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

RAW_DIR = "data"
PROCESSED_DIR = "chunks"
METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")
EMBEDDER_NAME = "BAAI/bge-small-en-v1.5"


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _chunk_text(text: str, window_size: int = 3, overlap: int = 1) -> list[str]:
    """Split text into overlapping sentence-window chunks."""
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    clean: list[str] = []
    for s in raw_sentences:
        s = s.strip()
        if not s or re.match(r"^[-_=*]+$", s):
            continue
        if s.startswith("Title:") or s.startswith("Author:"):
            continue
        clean.append(s)

    chunks: list[str] = []
    step = window_size - overlap
    for i in range(0, len(clean), step):
        window = clean[i : i + window_size]
        if not window:
            continue
        chunks.append(" ".join(window))
        if i + window_size >= len(clean):
            break
    return chunks


def _load_metadata() -> dict:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_metadata(metadata: dict) -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    sorted_meta = dict(sorted(metadata.items()))
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_meta, f, indent=4)


def _rebuild_embeddings(metadata: dict, embedder: SentenceTransformer) -> None:
    """Re-encode all chunks in metadata order and save the embeddings matrix."""
    ordered_keys = sorted(metadata.keys())
    texts: list[str] = []
    for chunk_file in ordered_keys:
        path = os.path.join(PROCESSED_DIR, chunk_file)
        with open(path, "r", encoding="utf-8") as f:
            texts.append(f.read())

    if texts:
        embeddings = embedder.encode(
            texts, batch_size=64, show_progress_bar=False, convert_to_numpy=True
        )
    else:
        embeddings = np.empty((0, 384), dtype=np.float32)

    np.save(EMBEDDINGS_FILE, embeddings)


def ingest_files(filenames: Optional[list[str]] = None) -> dict:
    """
    Chunk and embed the given filenames from RAW_DIR (or all files if None).
    Skips files whose mtime hasn't changed since the last ingestion.
    Clears the in-memory search-index caches after writing new embeddings.

    Returns {"processed": [...], "skipped": [...]}
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    existing_meta = _load_metadata()

    # Build a quick lookup: source_document -> {mtime, chunks}
    source_tracking: dict[str, dict] = {}
    for chunk_name, info in existing_meta.items():
        src = info.get("source_document")
        if src:
            if src not in source_tracking:
                source_tracking[src] = {"chunks": [], "mtime": info.get("source_mtime", 0)}
            source_tracking[src]["chunks"].append(chunk_name)

    # Decide which files need processing
    candidate_files = (
        filenames
        if filenames is not None
        else [f for f in os.listdir(RAW_DIR) if f.endswith(".txt")]
    )

    to_process: list[tuple[str, float]] = []
    skipped: list[str] = []
    for filename in candidate_files:
        file_path = os.path.join(RAW_DIR, filename)
        if not os.path.exists(file_path):
            continue
        mtime = os.path.getmtime(file_path)
        if filename in source_tracking and source_tracking[filename]["mtime"] == mtime:
            skipped.append(filename)
        else:
            to_process.append((filename, mtime))

    if not to_process:
        return {"processed": [], "skipped": skipped}

    device = _get_device()
    embedder = SentenceTransformer(EMBEDDER_NAME, device=device)

    # Remove stale chunks for files that will be re-processed
    for filename, _ in to_process:
        if filename in source_tracking:
            for old_chunk in source_tracking[filename]["chunks"]:
                old_path = os.path.join(PROCESSED_DIR, old_chunk)
                if os.path.exists(old_path):
                    os.remove(old_path)

    # Determine the next global chunk counter from existing metadata
    existing_indices = [
        int(c.split("_")[-1].split(".")[0])
        for c in existing_meta.keys()
        if c.split("_")[-1].split(".")[0].isdigit()
    ]
    chunk_counter = max(existing_indices, default=0)

    # Keep metadata entries for files we are NOT re-processing
    new_meta: dict = {}
    for chunk_name, info in existing_meta.items():
        src = info.get("source_document")
        if src and src not in [f for f, _ in to_process]:
            new_meta[chunk_name] = info

    processed: list[str] = []
    for filename, mtime in to_process:
        file_path = os.path.join(RAW_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        if not content:
            continue

        base_name = os.path.splitext(filename)[0]
        for chunk_text in _chunk_text(content):
            chunk_counter += 1
            chunk_filename = f"{base_name}_block_{chunk_counter}.txt"
            chunk_path = os.path.join(PROCESSED_DIR, chunk_filename)
            with open(chunk_path, "w", encoding="utf-8") as out_f:
                out_f.write(chunk_text)
            new_meta[chunk_filename] = {"source_document": filename, "source_mtime": mtime}

        processed.append(filename)

    _save_metadata(new_meta)
    _rebuild_embeddings(new_meta, embedder)

    return {"processed": processed, "skipped": skipped}


def remove_document(filename: str) -> bool:
    """
    Delete a source file from RAW_DIR, remove all its chunk files, rebuild
    the embeddings matrix, and invalidate caches.
    Returns True if the document existed and was removed, False otherwise.
    """
    file_path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(file_path):
        return False

    os.remove(file_path)

    existing_meta = _load_metadata()
    new_meta = {}
    for chunk_name, info in existing_meta.items():
        if info.get("source_document") == filename:
            chunk_path = os.path.join(PROCESSED_DIR, chunk_name)
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
        else:
            new_meta[chunk_name] = info

    _save_metadata(new_meta)

    device = _get_device()
    embedder = SentenceTransformer(EMBEDDER_NAME, device=device)
    _rebuild_embeddings(new_meta, embedder)

    return True


def list_documents() -> list[dict]:
    """Return a list of all source documents in RAW_DIR with their metadata."""
    if not os.path.exists(RAW_DIR):
        return []

    meta = _load_metadata()
    # Build set of indexed filenames
    indexed: set[str] = {info.get("source_document", "") for info in meta.values()}

    docs = []
    for filename in sorted(os.listdir(RAW_DIR)):
        if not filename.endswith(".txt"):
            continue
        file_path = os.path.join(RAW_DIR, filename)
        docs.append(
            {
                "filename": filename,
                "size_bytes": os.path.getsize(file_path),
                "status": "ready" if filename in indexed else "unindexed",
            }
        )
    return docs



