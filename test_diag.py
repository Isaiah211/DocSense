import sys
sys.path.insert(0, '.')

# Step 1: Write content to the file (simulating what upload does)
content = b'RAG stands for Retrieval Augmented Generation. It combines retrieval systems with generative AI models.'
with open('data/RAG systems.txt', 'wb') as f:
    f.write(content)
print(f'File written. Size: {len(content)} bytes')

import os
print(f'File size on disk: {os.path.getsize("data/RAG systems.txt")}')

# Step 2: Try ingesting it
from app.ingest import ingest_files
result = ingest_files(['RAG systems.txt'])
print(f'Ingest result: {result}')

# Step 3: Check for chunks
import glob
chunks = glob.glob('chunks/RAG*')
print(f'RAG chunks created: {chunks}')

# Read one if exists
if chunks:
    with open(chunks[0], 'r') as f:
        print(f'Chunk content: {f.read()}')

# Step 4: Check metadata
from semantic_search_utils import load_metadata
meta = load_metadata()
new = [k for k in meta if k.startswith('RAG')]
print(f'RAG metadata entries: {new}')

# Step 5: Search for it
from semantic_search_utils import search_chunks
result = search_chunks('Retrieval Augmented Generation', top_k=3)
print('\nSearch results:')
for r in result['results']:
    print(f'  [{r["rank"]}] {r["chunk_name"]}: score={r["similarity_score"]:.4f}')
    print(f'    Source: {r["metadata"].get("source_document", "unknown")}')
    if 'RAG' in r['chunk_name']:
        print('    *** NEW DOCUMENT FOUND IN SEARCH ***')

print('\n=== DIAGNOSTIC COMPLETE ===')