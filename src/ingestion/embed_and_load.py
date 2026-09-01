import json
import psycopg2
import gc
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values

def main():
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        dbname="legal_rag",
        user="obaid",
        password="mysecretpassword",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            source_file TEXT,
            chunk_index INTEGER,
            content TEXT,
            embedding vector(384)
        );
    """)
    cursor.execute("TRUNCATE document_chunks;")
    conn.commit()

    print("Reading chunks from data/processed/chunks.json...")
    with open("data/processed/chunks.json", "r") as f:
        chunks = json.load(f)

    # Drastically reduce batch size for WSL memory constraints
    batch_size = 32
    total_batches = (len(chunks) // batch_size) + 1

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        
        # Dynamically handle key names based on which extract script was used
        source_files = [c.get("source_file") or c.get("doc_id", "unknown") for c in batch]
        chunk_indices = [c.get("chunk_index") or c.get("chunk_id", 0) for c in batch]

        print(f"Embedding and inserting batch {i//batch_size + 1}/{total_batches}...")
        embeddings = model.encode(texts)

        records = [
            (src, idx, txt, emb.tolist())
            for src, idx, txt, emb in zip(source_files, chunk_indices, texts, embeddings)
        ]

        execute_values(
            cursor,
            "INSERT INTO document_chunks (source_file, chunk_index, content, embedding) VALUES %s",
            records
        )
        conn.commit()
        
        # Aggressively free memory after every batch
        del embeddings
        del records
        gc.collect()

    print("All chunks embedded and loaded into pgvector.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
