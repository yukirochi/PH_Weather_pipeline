import psycopg2

DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'weather_db'
DB_USER = 'weather_user'
DB_PASSWORD = 'weather_pass'

with psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
) as conn:
    with conn.cursor() as cur:
        
        query = "SELECT * FROM staging.stg_data"
        cur.execute(query)
        results = cur.fetchall()
        
        print(len(results))
