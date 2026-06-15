import os
import json
import re
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

def chunk_text_by_sentence_window(text, window_size=3, overlap=1):
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    clean_sentences = []
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence or re.match(r'^[-_=*]+$', sentence):
            continue
        if sentence.startswith("Title:") or sentence.startswith("Author:"):
            continue
        clean_sentences.append(sentence)
        
    chunks = []
    step = window_size - overlap
    for i in range(0, len(clean_sentences), step):
        window = clean_sentences[i:i + window_size]
        if not window:
            continue
        chunks.append(" ".join(window))
        if i + window_size >= len(clean_sentences):
            break
    return chunks

def main():
    RAW_DIR = "data"
    PROCESSED_DIR = "chunks"
    METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
    EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    existing_metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)

    source_tracking = {}
    for chunk_name, info in existing_metadata.items():
        src = info.get("source_document")
        if src:
            if src not in source_tracking:
                source_tracking[src] = {"chunks": [], "mtime": info.get("source_mtime", 0)}
            source_tracking[src]["chunks"].append(chunk_name)

    current_raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".txt")]
    files_to_process = []
    files_to_skip = []
    
    for filename in current_raw_files:
        file_path = os.path.join(RAW_DIR, filename)
        current_mtime = os.path.getmtime(file_path)
        if filename in source_tracking and source_tracking[filename]["mtime"] == current_mtime:
            files_to_skip.append(filename)
        else:
            files_to_process.append((filename, current_mtime))

    new_metadata_registry = {}
    all_chunks_to_keep = {}
    
    for filename in files_to_skip:
        for chunk_name, info in existing_metadata.items():
            if info.get("source_document") == filename:
                new_metadata_registry[chunk_name] = info
                all_chunks_to_keep[chunk_name] = True

    if not files_to_process:
        print("All chunks up to date on disk.")
        return

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"\n--- RUNNING FAST INGESTION ({device.upper()}) ---")
    embedder = SentenceTransformer("BAAI/bge-small-en-v1.5", device=device)

    # Clear out older chunk files for modified raw files
    for filename, _ in files_to_process:
        if filename in source_tracking:
            for old_chunk in source_tracking[filename]["chunks"]:
                old_chunk_path = os.path.join(PROCESSED_DIR, old_chunk)
                if os.path.exists(old_chunk_path):
                    os.remove(old_chunk_path)

    chunk_global_counter = max([int(c.split("_")[-1].split(".")[0]) for c in existing_metadata.keys()] + [0])

    print("Slicing text files...")
    for filename, mtime in files_to_process:
        file_path = os.path.join(RAW_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read().strip()
        if not actual_content:
            continue

        window_chunks = chunk_text_by_sentence_window(actual_content, window_size=3, overlap=1)
        base_name, _ = os.path.splitext(filename)

        for chunk_text in window_chunks:
            chunk_global_counter += 1
            chunk_filename = f"{base_name}_block_{chunk_global_counter}.txt"
            
            with open(os.path.join(PROCESSED_DIR, chunk_filename), "w", encoding="utf-8") as out_f:
                out_f.write(chunk_text)

            new_metadata_registry[chunk_filename] = {
                "source_document": filename,
                "source_mtime": mtime
            }
            all_chunks_to_keep[chunk_filename] = True

    for disk_file in os.listdir(PROCESSED_DIR):
        if disk_file.endswith(".txt") and disk_file not in all_chunks_to_keep:
            os.remove(os.path.join(PROCESSED_DIR, disk_file))

    print("\nGenerating and saving vector embeddings matrix cache...")
    chunks_text_list = []
    ordered_keys = sorted(new_metadata_registry.keys())
    for chunk_file in ordered_keys:
        with open(os.path.join(PROCESSED_DIR, chunk_file), "r", encoding="utf-8") as cf:
            chunks_text_list.append(cf.read())

    # Generates embeddings instantly in large parallel batches
    embeddings = embedder.encode(chunks_text_list, batch_size=64, show_progress_bar=True, convert_to_numpy=True)
    np.save(EMBEDDINGS_FILE, embeddings)

    sorted_metadata = {k: new_metadata_registry[k] for k in ordered_keys}
    with open(METADATA_FILE, "w", encoding="utf-8") as meta_f:
        json.dump(sorted_metadata, meta_f, indent=4)

    print("-> Ingestion complete!\n")

if __name__ == "__main__":
    main()