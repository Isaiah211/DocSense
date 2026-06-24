import os

from semantic_search_utils import get_search_assets_exist, search_chunks

def main():
    PROCESSED_DIR = "chunks"
    CONFIG_FILE = "Labels.json"

    if not get_search_assets_exist():
        print("Error: Missing database files or Labels.json template configuration.")
        return

    print("--- UPGRADED DYNAMIC SEARCH ENGINE ACTIVE ---")
    print("System ready for text inquiries.\n")

    while True:
        user_question = input("Ask a question (type 'exit' to close): ").strip()
        if user_question.lower() == 'exit' or not user_question:
            break

        search_result = search_chunks(user_question, top_k=3)
        detected_labels = [f"{item['id']} ({item['score']*100:.1f}%)" for item in search_result["detected_labels"]]

        print(f"-> Dynamic Classified Intents: {detected_labels}")

        results = search_result["results"]
        top_k = len(results)

        print("\n=========================================================")
        print(f"               TOP {top_k} SEMANTIC MATCHES                     ")
        print("=========================================================")
        for result in results:
            file_name = result["chunk_name"]
            text_content = result["text"]
            
            print(f"Option [{result['rank']}] (Relevance Match Score: {result['boosted_percentage']:.2f}%)")
            print(f"  Source Chunk Path: .../{PROCESSED_DIR}/{file_name}")
            print(f"  Snippet Excerpt:\n\"\"\"\n{text_content.strip()}\n\"\"\"")
            print("-" * 57)
        print("\n" + "="*57 + "\n")

if __name__ == "__main__":
    main()