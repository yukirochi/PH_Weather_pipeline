import requests
import psycopg2  # type: ignore[import]
from psycopg2.extras import Json
from datetime import datetime, timezone

url = 'https://api.open-meteo.com/v1/forecast?latitude=14.759&longitude=121.2019&current=temperature_2m,rain,wind_speed_10m&timezone=Asia%2FManila'

response = requests.get(url)
response.raise_for_status()   # fail loudly if the API call itself failed
data = response.json()

conn = psycopg2.connect(
    host="localhost",      # or "postgres_weather" if this script itself runs inside Docker
    port=5433,
    user="weather_user",
    password="weather_pass",
    dbname="weather_db"
)

try:
    cur = conn.cursor()

    current = data["current"]

    cur.execute(
        """
        INSERT INTO raw.weather_observations
            (latitude, longitude, observed_at, temperature_c,
             precipitation_mm, wind_speed_kmh, raw_payload, source_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (latitude, longitude, observed_at, source_name) DO NOTHING
        """,
        (
            data["latitude"],
            data["longitude"],
            current["time"],              # e.g. "2026-07-06T14:00"
            current.get("temperature_2m"),
            current.get("rain"),
            current.get("wind_speed_10m"),
            Json(data),                    # full raw response, preserved
            "open-meteo"
        )
    )

    conn.commit()
    cur.close()

finally:
    conn.close()