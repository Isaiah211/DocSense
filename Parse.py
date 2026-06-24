import os
import re
import pandas as pd

# Load your CSV file
file_path = "articles.csv"
df = pd.read_csv(file_path)

# Create a folder to store the extracted articles
output_folder = "extracted_articles"
os.makedirs(output_folder, exist_ok=True)

for idx, row in df.iterrows():
    title = str(row['title'])
    content = str(row['text'])
    author = str(row['author'])
    
    # 1. Clean the title so it's a valid filename
    # This removes characters like \, /, :, *, ?, ", <, >, |
    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
    
    # 2. Replace spaces or weird whitespace with single spaces, and strip edges
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    # 3. Truncate the title if it's too long (OS limit is usually 255 chars)
    if len(clean_title) > 100:
        clean_title = clean_title[:100]
        
    # 4. Handle edge case: if the title becomes completely empty after cleaning
    if not clean_title:
        clean_title = f"article_{idx}"
        
    # Construct the final filepath
    filename = os.path.join(output_folder, f"{clean_title}.txt")
    
    # Write the article details into the text file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Author: {author}\n")
        f.write("-" * 40 + "\n\n")
        f.write(content)

print(f"Done! All articles have been saved to the '{output_folder}' directory.")