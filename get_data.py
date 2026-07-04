import requests
import psycopg2
import json
from datetime import datetime

url = 'https://api.open-meteo.com/v1/forecast?latitude=14.759&longitude=121.2019&hourly=temperature_2m,rain,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FManila'

response = requests.get(url)
data = response.json()

conn = psycopg2.connect(
    host="localhost",      # or "postgres_weather" if this script itself runs inside Docker
    port=5433,
    user="weather_user",
    password="weather_pass",
    dbname="weather_db"
)

cur = conn.cursor()

cur.execute(
    "INSERT INTO raw.weather_api_response (fetched_at, raw_json) VALUES (%s, %s)",
    (datetime.now(), json.dumps(data))
)

conn.commit()
cur.close()
conn.close