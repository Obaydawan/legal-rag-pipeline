import streamlit as st
import os
import psycopg2
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Page Configuration
st.set_page_config(page_title="Legal RAG Assistant", page_icon="⚖️", layout="centered")
st.title("⚖️ Legal Contracts AI Assistant")
st.markdown("Ask questions about your ingested legal documents. The AI will cite specific clauses to answer.")

# 2. Cache Heavy Resources (Load Once)
@st.cache_resource
def load_models():
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    # Ensure the API key is picked up from the environment
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return embedder, client

embedder, client = load_models()

# 3. Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if prompt := st.chat_input("E.g., What are the confidentiality obligations?"):
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Searching contracts and generating response..."):
        try:
            # --- RETRIEVAL PHASE ---
            query_embedding = embedder.encode(prompt).tolist()

            conn = psycopg2.connect(
                dbname="legal_rag",
                user="obaid",
                password="mysecretpassword",
                host="localhost",
                port="5432"
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT content 
                FROM document_chunks 
                ORDER BY embedding <=> %s::vector 
                LIMIT 3;
            """, (query_embedding,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # --- GENERATION PHASE ---
            if not results:
                response_text = "I couldn't find any relevant clauses in the database."
            else:
                context = "\n\n---\n\n".join([row[0] for row in results])
                
                system_prompt = f"""
                You are an expert legal assistant. Answer the user's question based ONLY on the provided contract excerpts.
                If the answer is not contained in the excerpts, say "I cannot answer this based on the provided documents."
                
                Context Documents:
                {context}
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]

                response = client.chat.completions.create(
                    messages=messages,
                    model="openai/gpt-oss-20b",
                    temperature=0.2,
                )
                
                response_text = response.choices[0].message.content

        except Exception as e:
            response_text = f"An error occurred: {str(e)}"

    # Show AI response
    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
