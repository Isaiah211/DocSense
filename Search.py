import os
import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

def main():
    PROCESSED_DIR = "chunks"
    METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
    EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")

    if not os.path.exists(METADATA_FILE) or not os.path.exists(EMBEDDINGS_FILE):
        print(f"Error: Missing index mappings in '{PROCESSED_DIR}/'. Run 'ingest_chunks.py' first.")
        return

    # Load structural maps and binary embeddings caches from the chunks/ directory
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    doc_embeddings = np.load(EMBEDDINGS_FILE)

    chunks_text = []
    chunks_filenames = []
    for chunk_file in metadata.keys():
        chunk_path = os.path.join(PROCESSED_DIR, chunk_file)
        with open(chunk_path, "r", encoding="utf-8") as cf:
            chunks_text.append(cf.read())
        chunks_filenames.append(chunk_file)

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"--- SEARCH ENGINE INTERACTIVE SYSTEM ({device.upper()}) ---")
    embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    print("System active and responsive.\n")

    while True:
        user_question = input("Ask a question (type 'exit' to close): ").strip()
        if user_question.lower() == 'exit' or not user_question:
            break

        query_embedding = embedder.encode(user_question, convert_to_tensor=True, device=device)
        doc_embeddings_tensor = torch.from_numpy(doc_embeddings).to(device)

        similarity_scores = util.cos_sim(query_embedding, doc_embeddings_tensor)[0]
        
        top_k = min(3, len(chunks_text))
        top_indices = similarity_scores.argsort(descending=True)[:top_k]

        print("\n=========================================================")
        print(f"               TOP {top_k} OPTIMIZED SEARCH RESULTS             ")
        print("=========================================================")
        
        for rank, index_tensor in enumerate(top_indices, 1):
            idx = index_tensor.item()
            score = similarity_scores[idx].item()
            file_name = chunks_filenames[idx]
            
            ai_tags = metadata[file_name]["labels"]
            text_content = chunks_text[idx]
            
            print(f"Option [{rank}] (Semantic Match Confidence Score: {score * 100:.2f}%)")
            print(f"  Source Chunk Path: .../{PROCESSED_DIR}/{file_name}")
            print(f"  Assigned Categories: {ai_tags}")
            print(f"  Snippet Excerpt:\n\"\"\"\n{text_content.strip()}\n\"\"\"")
            print("-" * 57)
        print("\n" + "="*57 + "\n")

if __name__ == "__main__":
    main()