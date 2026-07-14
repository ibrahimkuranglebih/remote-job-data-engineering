from airflow import DAG
import pendulum
import os
import sys
sys.path.append(os.path.dirname(__file__))

from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

from extract.extract import extract_jobs
from transform.transform_stagging import run_stagging_transform
from load.load_stagging import run_stagging_load
from transform.transform_mart import run_transform_mart
from load.load_mart import run_mart_load
    
local_time = pendulum.timezone("Asia/Jakarta")
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 1, 4),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
with DAG(
    dag_id = "remote_job_data_pipeline",
    start_date=pendulum.datetime(2026, 1, 4, tz=local_time),
    schedule="0 8,20 * * *",
    default_args=default_args,
    catchup=False,
    tags=['remote', 'pipeline','job']
) as dag :
    extract_jobs = PythonOperator(
        task_id = "extract_data_remote_jobs",
        python_callable = extract_jobs
    )
    
    transform_stagging = PythonOperator(
        task_id = "transform_data_remote_jobs",
        python_callable = run_stagging_transform
    )
    
    load_stagging = PythonOperator(
        task_id = "load_data_remote_jobs",
        python_callable = run_stagging_load
    )
    
    transform_mart = PythonOperator(
        task_id = "transform_data_remote_jobs_mart",
        python_callable = run_transform_mart
    )
    
    load_mart = PythonOperator(
        task_id = "load_data_remote_jobs_mart",
        python_callable = run_mart_load
    )

    extract_jobs >> transform_stagging >> load_stagging >> transform_mart >> load_mart