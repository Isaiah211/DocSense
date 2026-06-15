import os
import json
import numpy as np
import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer

def chunk_text_by_words(text, max_words=180):
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_word_count = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        words_in_para = len(para.split())
        if current_word_count + words_in_para > max_words and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_word_count = words_in_para
        else:
            current_chunk.append(para)
            current_word_count += words_in_para

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    return chunks

def main():
    RAW_DIR = "data"
    PROCESSED_DIR = "chunks"
    CONFIG_FILE = "Labels.json"
    
    METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
    EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")

    # Load from your newly named configuration file
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Missing configuration map '{CONFIG_FILE}'. Generating default template.")
        default_config = {"candidate_labels": ["Tech", "AI", "General"], "confidence_threshold": 0.50}
        with open(CONFIG_FILE, "w") as cf:
            json.dump(default_config, cf, indent=4)
    
    with open(CONFIG_FILE, "r") as cf:
        config_data = json.load(cf)
    
    CANDIDATE_LABELS = config_data.get("candidate_labels", ["General"])
    CONFIDENCE_THRESHOLD = config_data.get("confidence_threshold", 0.50)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    # Load existing indexing tracking metadata
    existing_metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)

    source_tracking = {}
    for chunk_name, info in existing_metadata.items():
        src = info.get("source_document")
        mtime = info.get("source_mtime", 0)
        if src:
            if src not in source_tracking:
                source_tracking[src] = {"chunks": [], "mtime": mtime}
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

    all_chunks_to_keep = {}
    new_metadata_registry = {}
    
    for filename in files_to_skip:
        print(f"-> [SAFEGUARD MATCH] Skipping unmodified raw document: '{filename}'")
        for chunk_name, info in existing_metadata.items():
            if info.get("source_document") == filename:
                new_metadata_registry[chunk_name] = info
                all_chunks_to_keep[chunk_name] = True

    if not files_to_process:
        print("\nAll database structures are perfectly up-to-date. No chunking needed.")
        return

    # Hardware acceleration check
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"\n--- SPINNING UP AI ENGINES ({device.upper()}) ---")
    classifier_ai = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=0 if device == "cuda" else -1)
    embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)

    for filename, _ in files_to_process:
        if filename in source_tracking:
            print(f"-> Refreshing outdated chunks for modified file: '{filename}'")
            for old_chunk in source_tracking[filename]["chunks"]:
                old_chunk_path = os.path.join(PROCESSED_DIR, old_chunk)
                if os.path.exists(old_chunk_path):
                    os.remove(old_chunk_path)

    chunk_global_counter = max([int(c.split("_")[-1].split(".")[0]) for c in existing_metadata.keys()] + [0])

    for filename, mtime in files_to_process:
        file_path = os.path.join(RAW_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read().strip()
        if not actual_content:
            continue

        print(f"Processing and tagging: '{filename}'...")
        chunks = chunk_text_by_words(actual_content, max_words=180)
        base_name, _ = os.path.splitext(filename)

        for idx, chunk_text in enumerate(chunks, 1):
            chunk_global_counter += 1
            chunk_filename = f"{base_name}_chunk_{chunk_global_counter}.txt"
            chunk_path = os.path.join(PROCESSED_DIR, chunk_filename)

            with open(chunk_path, "w", encoding="utf-8") as out_f:
                out_f.write(chunk_text)

            ai_result = classifier_ai(chunk_text, candidate_labels=CANDIDATE_LABELS, multi_label=True)
            assigned_labels = [l for l, s in zip(ai_result["labels"], ai_result["scores"]) if s >= CONFIDENCE_THRESHOLD]
            if not assigned_labels:
                assigned_labels = [ai_result["labels"][0]]

            new_metadata_registry[chunk_filename] = {
                "labels": assigned_labels,
                "source_document": filename,
                "source_mtime": mtime
            }
            all_chunks_to_keep[chunk_filename] = True

    for disk_file in os.listdir(PROCESSED_DIR):
        if disk_file.endswith(".txt") and disk_file not in all_chunks_to_keep:
            os.remove(os.path.join(PROCESSED_DIR, disk_file))

    print("\nUpdating vectorized binary cache matrices...")
    chunks_text_list = []
    ordered_keys = sorted(new_metadata_registry.keys())
    
    for chunk_file in ordered_keys:
        with open(os.path.join(PROCESSED_DIR, chunk_file), "r", encoding="utf-8") as cf:
            chunks_text_list.append(cf.read())

    embeddings = embedder.encode(chunks_text_list, show_progress_bar=True, convert_to_numpy=True)
    np.save(EMBEDDINGS_FILE, embeddings)

    sorted_metadata = {k: new_metadata_registry[k] for k in ordered_keys}