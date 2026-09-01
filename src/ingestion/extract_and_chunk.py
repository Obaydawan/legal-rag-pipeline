import os
import json

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
CHUNK_SIZE = 1000
OVERLAP = 200

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

def main():
    all_chunks = []
    
    # Fail-safe: Create a sample document if the raw folder is empty
    if not os.listdir(RAW_DIR):
        print(f"No files found in {RAW_DIR}. Creating a sample legal document...")
        with open(os.path.join(RAW_DIR, "sample_contract.txt"), "w") as f:
            f.write("This is a sample legal contract for the RAG pipeline. " * 100)

    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".txt"):
            with open(os.path.join(RAW_DIR, filename), "r", encoding="utf-8") as f:
                text = f.read()
                chunks = chunk_text(text, CHUNK_SIZE, OVERLAP)
                for i, chunk in enumerate(chunks):
                    all_chunks.append({"doc_id": filename, "chunk_id": i, "text": chunk})

    output_file = os.path.join(PROCESSED_DIR, "chunks.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=4)
        
    print(f"Successfully extracted and generated {len(all_chunks)} chunks.")

if __name__ == "__main__":
    main()
