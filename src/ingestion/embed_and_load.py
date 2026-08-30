import json
import psycopg2
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

    print("Reading chunks from data/processed/chunks.jsonl...")
    with open("data/processed/chunks.jsonl", "r") as f:
        chunks = [json.loads(line) for line in f]

    batch_size = 500
    total_batches = (len(chunks) // batch_size) + 1
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        
        print(f"Embedding and inserting batch {i//batch_size + 1}/{total_batches}...")
        embeddings = model.encode(texts)

        records = [
            (c["source_file"], c["chunk_index"], c["text"], emb.tolist())
            for c, emb in zip(batch, embeddings)
        ]

        execute_values(
            cursor,
            "INSERT INTO document_chunks (source_file, chunk_index, content, embedding) VALUES %s",
            records
        )
        conn.commit()

    print("All chunks embedded and loaded into pgvector.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
