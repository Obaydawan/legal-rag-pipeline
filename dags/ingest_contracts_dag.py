from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

PROJECT_ROOT = os.path.expanduser("~/projects/legal-rag-pipeline")

default_args = {
    'owner': 'obaid',
    'depends_on_past': False,
    'start_date': datetime(2026, 8, 30),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'legal_contracts_rag_pipeline',
    default_args=default_args,
    description='Extract, chunk, embed, and load legal contracts',
    schedule=None, 
    catchup=False,
    tags=['legal_rag'],
) as dag:

    extract_and_chunk = BashOperator(
        task_id='extract_and_chunk',
        bash_command=f'cd {PROJECT_ROOT} && source venv/bin/activate && python3 src/ingestion/extract_and_chunk.py'
    )

    embed_and_load = BashOperator(
        task_id='embed_and_load',
        bash_command=f'cd {PROJECT_ROOT} && source venv/bin/activate && python3 src/ingestion/embed_and_load.py'
    )

    extract_and_chunk >> embed_and_load
