import requests
import psycopg2  # type: ignore[import]
from psycopg2.extras import Json
from datetime import datetime, timezone
from datetime import time as dt_time  # if you need datetime.time elsewhere
import time  # the actual time module, for time.sleep

CITIES = [
    {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842},
    {"name": "Cebu",   "latitude": 10.3157, "longitude": 123.8854},
    {"name": "Davao",  "latitude": 7.1907,  "longitude": 125.4553},
    {"name": "Baguio", "latitude": 16.4023, "longitude": 120.5960},
    {"name": "Iloilo", "latitude": 10.7202, "longitude": 122.5621},
]


DELAY = 2
MAX_RETRIES = 3

BASE_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_VARS = "temperature_2m,rain,wind_speed_10m"
TIMEZONE = "Asia/Manila"
SOURCE_NAME = "open-meteo"


conn = psycopg2.connect(
    host="localhost",      # or "postgres_weather" if this script itself runs inside Docker
    port=5433,
    user="weather_user",
    password="weather_pass",
    dbname="weather_db"
)

def build_url(city: dict) -> str:
    return (
        f"{BASE_URL}?latitude={city['latitude']}&longitude={city['longitude']}"
        f"&current={CURRENT_VARS}&timezone={TIMEZONE.replace('/', '%2F')}"
    )
    
    
def fetch_data(city: dict) -> dict:
    url = build_url(city)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url)
            response.raise_for_status()   # fail loudly if the API call itself failed
            return response.json()
        except requests.RequestException as e:
            print(f"Attempt {attempt} failed for {city['name']}: {e}")
            if attempt == MAX_RETRIES:
                return None  # or raise an exception, depending on your needs
            delay = DELAY * (2 ** (attempt - 1))
            print(f"[{city['name']}] attempt {attempt} failed ({e}), retrying in {delay}s...")
            time.sleep(delay)
    
    return None  # If all attempts fail, return None or handle as needed


def insert_observation(cur, city: dict, data: dict) -> None:
    current = data["current"]
 
    cur.execute(
        """
        INSERT INTO raw.weather_observations
            (city_name, latitude, longitude, observed_at, temperature_c,
             precipitation_mm, wind_speed_kmh, raw_payload, source_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (latitude, longitude, observed_at, source_name)
        DO UPDATE SET
            temperature_c     = EXCLUDED.temperature_c,
            precipitation_mm  = EXCLUDED.precipitation_mm,
            wind_speed_kmh    = EXCLUDED.wind_speed_kmh,
            raw_payload       = EXCLUDED.raw_payload,
            city_name         = EXCLUDED.city_name,
            ingested_at       = now();
        """,
        (
            city["name"],
            data["latitude"],
            data["longitude"],
            current["time"],
            current.get("temperature_2m"),
            current.get("rain"),
            current.get("wind_speed_10m"),
            Json(data),
            SOURCE_NAME,
        ),
    )

def main():
 
    try:
        cur = conn.cursor()
 
        for city in CITIES:
            print(f"Fetching {city['name']}...")
            data = fetch_data(city)
 
            if data is None:
                # Skip this city, keep going for the rest — one bad source
                # shouldn't block the other 4 (or the other 99, at scale).
                continue
 
            insert_observation(cur, city, data)
            conn.commit()
            print(f"[{city['name']}] inserted OK")
 
        cur.close()
 
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    main()
 


