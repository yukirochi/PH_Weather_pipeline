import psycopg2
from dotenv import load_dotenv
import os
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd

load_dotenv()

DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'weather_db'
DB_USER = 'weather_user'
DB_PASSWORD = 'weather_pass'

snow_user = os.getenv('SNOW_USER')
snow_pass = os.getenv('SNOW_PASS')
snow_acc = os.getenv('SNOW_ACC')
snow_wh = os.getenv('SNOW_WH')
snow_db = os.getenv('SNOW_DB')
snow_schema = os.getenv('SNOW_SCHEMA')

df = None
with psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
) as conn:
    query = "SELECT * FROM staging.stg_data"
    df = pd.read_sql_query(query, conn)


df.columns = df.columns.str.upper()


snow_conn = snowflake.connector.connect(
    user=snow_user,
    password=snow_pass,
    account=snow_acc,
    warehouse=snow_wh,
    database=snow_db,
    schema=snow_schema
)

success = write_pandas(
    conn=snow_conn,
    df=df,
    table_name='STG_DATA'
)

if success:
    print('sucess')

conn.close()