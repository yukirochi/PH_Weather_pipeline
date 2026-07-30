import psycopg2
from dotenv import load_dotenv
import os
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd

load_dotenv()

snow_user = os.getenv('SNOW_USER')
snow_pass = os.getenv('SNOW_PASS')
snow_acc = os.getenv('SNOW_ACC')
snow_wh = os.getenv('SNOW_WH')
snow_db = os.getenv('SNOW_DB')
snow_schema = os.getenv('SNOW_SCHEMA')

df = None
with psycopg2.connect(
    host="postgres_weather",     
    port=5432,
    user="weather_user",
    password="weather_pass",
    dbname="weather_db"
) as conn:
    query = "SELECT * FROM staging.stg_data ORDER BY id DESC LIMIT 120"
    df = pd.read_sql_query(query, conn)


df.columns = df.columns.str.upper()

print(df.head())

snow_conn = snowflake.connector.connect(
    user=snow_user,
    password=snow_pass,
    account=snow_acc,
    warehouse=snow_wh,
    database=snow_db,
    schema=snow_schema
)


snow_conn.cursor().execute("""
        CREATE TEMPORARY TABLE STAGING_DATA 
        LIKE STG_DATA
    """)


success = write_pandas(
    conn=snow_conn,
    df=df,
    table_name='STAGING_DATA'
)

if success:
    
    merge_sql = """
        MERGE INTO
            STG_DATA AS target
            USING STAGING_DATA AS source
        ON target.OBSERVED_HOUR = source.OBSERVED_HOUR AND target.CITY_NAME = source.CITY_NAME AND source.OBSERVED_DATE = target.OBSERVED_DATE
        
        WHEN MATCHED THEN 
            UPDATE SET 
                target.PRECIPITATION_MM = source.PRECIPITATION_MM,
                target.TEMPERATURE_C = source.TEMPERATURE_C,
                target.WIND_SPEED_KMH = source.WIND_SPEED_KMH
        WHEN NOT MATCHED THEN
            INSERT(CITY_NAME, ID,LATITUDE,LONGITUDE,OBSERVED_DATE,OBSERVED_HOUR,PRECIPITATION_MM,TEMPERATURE_C,WIND_SPEED_KMH)
            VALUES(source.CITY_NAME, source.ID,source.LATITUDE,source.LONGITUDE,source.OBSERVED_DATE,source.OBSERVED_HOUR,source.PRECIPITATION_MM,source.TEMPERATURE_C,source.WIND_SPEED_KMH)
    """
    snow_conn.cursor().execute(merge_sql)
    print("sucess")

conn.close()