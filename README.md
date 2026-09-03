# Legal RAG Pipelin

End-to-end RAG pipeline for legal contracts using the CUAD (Contract Understanding Atticus Dataset).

## What this project does
1. Ingests and cleans 510 legal contracts from CUAD
2. Chunks the text with legal-document-aware noise removal
3. Generates embeddings using `all-MiniLM-L6-v2`
4. Stores vectors in PostgreSQL + pgvector
5. Orchestrates the whole flow with Apache Airflow 3

## Tech Stack
- Python 3.12
- sentence-transformers
- PostgreSQL + pgvector (Docker)
- Apache Airflow 3 (standalone)
- Docker Compose (named volumes)

## Project Structure
legal-rag-pipeline/
├── dags/                      # Airflow DAGs
├── src/ingestion/             # Chunking + embedding scripts
├── data/                      # (gitignored) raw + processed data
├── docker-compose.yml         # pgvector service
├── requirements.txt
└── README.md

## Quick Start
1. Clone the repo
2. Create virtualenv and install dependencies
3. Download CUAD dataset into `data/raw/full_contract_txt/`
4. `docker compose up -d`
5. Run the scripts or trigger the Airflow DAG

## Status
- Phase 4.2 (Ingestion & Chunking) — Complete
- Phase 4.3 (Embeddings + pgvector) — Complete
- Phase 4.4 (Airflow Orchestration) — In progress
