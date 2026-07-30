from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pendulum
default_args = {
    "owner": "otto",
    "retries": 2,                         # retry failed tasks twice
    "retry_delay": timedelta(minutes=5),  # wait 5 min between retries
}

my_start_date = pendulum.datetime(2026, 7, 31, 0, 0, tz="UTC")

with DAG(
    dag_id="to_snowflake",
    default_args=default_args,
    description="transfer_to_snowflake",
    start_date=my_start_date,   # fixed reference point for scheduling
    schedule="@daily",                # runs once every midnight
    catchup=False,                     # don't backfill missed past runs
    tags=["transfer_to_snowflake"],
) as dag:
    
    transfer_to_snowflake = BashOperator(
        task_id="transer_to_snowflake",
        bash_command="python /opt/airflow/scripts/single_transfer.py"
    )

    transfer_to_snowflake