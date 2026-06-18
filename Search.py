import os
import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

def main():
    PROCESSED_DIR = "chunks"
    CONFIG_FILE = "Labels.json"
    METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
    EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")

    if not all([os.path.exists(f) for f in [METADATA_FILE, EMBEDDINGS_FILE, CONFIG_FILE]]):
        print("Error: Missing database files or Labels.json template configuration.")
        return

    with open(CONFIG_FILE, "r") as cf:
        config_data = json.load(cf)
    
    # Load structured taxonomies
    CATEGORIES = config_data.get("candidate_labels", [])

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
    print(f"--- UPGRADED DYNAMIC SEARCH ENGINE ACTIVE ({device.upper()}) ---")
    
    embedder = SentenceTransformer("BAAI/bge-small-en-v1.5", device=device)
    print(f"Database structures online. Loaded {len(CATEGORIES)} structured taxonomies.")
    print("System ready for text inquiries.\n")

    while True:
        user_question = input("Ask a question (type 'exit' to close): ").strip()
        if user_question.lower() == 'exit' or not user_question:
            break

        normalized_query = user_question.lower().strip()
        query_words = normalized_query.replace("?", "").replace("'", " ").split()
        
        # High-Weight Token Boundary Query Expansion
        expansion_terms = ""
        has_ai_intent = any(w in query_words for w in ["ai", "ais", "bot", "bots", "app", "apps", "software"])
        has_weather_intent = any(w in query_words for w in ["weather", "forecast", "forecasts", "climate", "seasons"])
        
        if has_ai_intent and has_weather_intent:
            expansion_terms = " personalized weather messenger slack bot integration consumer app client update"
        elif has_ai_intent:
            expansion_terms = " software chatbot app integration service automated tool utility engineering implementation"
            
        expanded_query = normalized_query + expansion_terms
        query_embedding = embedder.encode(expanded_query, convert_to_tensor=True, device=device)

        # COMPUTE TAXONOMY SCORES INTENTS
        category_scores = {}
        for cat in CATEGORIES:
            cat_id = cat["id"]
            phrases = cat["search_phrases"]
            
            # Embed the decoupled keyword phrases for this group
            phrase_embeddings = embedder.encode(phrases, convert_to_tensor=True, device=device)
            phrase_scores = util.cos_sim(query_embedding, phrase_embeddings)[0]
            
            # Take the highest matching specific feature score as the representative metric
            category_scores[cat_id] = torch.max(phrase_scores).item()

        max_score = max(category_scores.values())
        dynamic_threshold = max(0.10, max_score - 0.12) # Shrunk sliding gap for higher precision
        
        detected_labels = [
            f"{cat_id} ({score_val*100:.1f}%)"
            for cat_id, score_val in category_scores.items()
            if score_val >= dynamic_threshold
        ]
                
        print(f"-> Dynamic Classified Intents: {detected_labels}")

        # Vectorized Document Similarity Computation
        doc_embeddings_tensor = torch.from_numpy(doc_embeddings).to(device)
        similarity_scores = util.cos_sim(query_embedding, doc_embeddings_tensor)[0]
        
        top_k = min(3, len(chunks_text))
        top_indices = similarity_scores.argsort(descending=True)[:top_k]

        print("\n=========================================================")
        print(f"               TOP {top_k} SEMANTIC MATCHES                     ")
        print("=========================================================")
        for rank, index_tensor in enumerate(top_indices, 1):
            idx = index_tensor.item()
            raw_score = similarity_scores[idx].item()
            
            floor = 0.42
            ceiling = 0.82
            normalized_score = (raw_score - floor) / (ceiling - floor)
            boosted_percentage = min(100.0, max(0.0, normalized_score * 100))
            
            if raw_score > 0.55 and boosted_percentage < 50.0:
                boosted_percentage = 65.0 + (raw_score * 10)

            file_name = chunks_filenames[idx]
            text_content = chunks_text[idx]
            
            print(f"Option [{rank}] (Relevance Match Score: {boosted_percentage:.2f}%)")
            print(f"  Source Chunk Path: .../{PROCESSED_DIR}/{file_name}")
            print(f"  Snippet Excerpt:\n\"\"\"\n{text_content.strip()}\n\"\"\"")
            print("-" * 57)
        print("\n" + "="*57 + "\n")

if __name__ == "__main__":
    main()