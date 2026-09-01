import os
import psycopg2
from sentence_transformers import SentenceTransformer
from groq import Groq

def main():
    # 1. Initialize the embedding model and Groq client
    print("Loading embedding model...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # 2. Get the user's question
    user_query = input("\nAsk a question about your contracts: ")
    query_embedding = embedder.encode(user_query).tolist()

    # 3. Connect to the database and retrieve relevant chunks
    print("\nSearching database for relevant clauses...")
    conn = psycopg2.connect(
        dbname="legal_rag",
        user="obaid",
        password="mysecretpassword",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    # Perform a vector similarity search (cosine distance)
    cursor.execute("""
        SELECT content 
        FROM document_chunks 
        ORDER BY embedding <=> %s::vector 
        LIMIT 3;
    """, (query_embedding,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        print("No relevant context found in the database.")
        return

    # 4. Construct the prompt with the retrieved context
    context = "\n\n---\n\n".join([row[0] for row in results])
    
    prompt = f"""
    You are an expert legal assistant. Answer the user's question based ONLY on the provided contract excerpts.
    If the answer is not contained in the excerpts, say "I cannot answer this based on the provided documents."
    
    Context Documents:
    {context}
    
    User Question: {user_query}
    """

    # 5. Generate the answer using Llama 3
    print("Generating answer...\n")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-20b",
        temperature=0.2,
    )

    print("================ RAG RESPONSE ================")
    print(response.choices[0].message.content)
    print("==============================================")

if __name__ == "__main__":
    main()
