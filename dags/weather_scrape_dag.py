from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "otto",
    "retries": 2,                         # retry failed tasks twice
    "retry_delay": timedelta(minutes=5),  # wait 5 min between retries
}

with DAG(
    dag_id="weather_scrape_and_load",
    default_args=default_args,
    description="Scrape weather data and load into Postgres",
    start_date=datetime(2026, 7, 1),   # fixed reference point for scheduling
    schedule="@hourly",                # runs once every hour
    catchup=False,                     # don't backfill missed past runs
    tags=["weather"],
) as dag:
    
    scrape_and_load = BashOperator(
        task_id="scrape_and_load_weather",
        bash_command="python /opt/airflow/scripts/get_data.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/weather_dbt && dbt run",
    )

    scrape_and_load >> dbt_run