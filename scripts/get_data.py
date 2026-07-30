import requests
import psycopg2  # type: ignore[import]
from psycopg2.extras import Json
from datetime import datetime, timezone
from datetime import time as dt_time  # if you need datetime.time elsewhere
import time  # the actual time module, for time.sleep
import os
CITIES = [
    # NCR - National Capital Region
    {"name": "Manila",       "region": "NCR", "latitude": 14.5995, "longitude": 120.9842},
    {"name": "Quezon City",  "region": "NCR", "latitude": 14.6760, "longitude": 121.0437},
    {"name": "Caloocan",     "region": "NCR", "latitude": 14.6488, "longitude": 120.9673},
    {"name": "Las Piñas",    "region": "NCR", "latitude": 14.4499, "longitude": 120.9829},
    {"name": "Makati",       "region": "NCR", "latitude": 14.5547, "longitude": 121.0244},
    {"name": "Malabon",      "region": "NCR", "latitude": 14.6681, "longitude": 120.9569},
    {"name": "Mandaluyong",  "region": "NCR", "latitude": 14.5794, "longitude": 121.0359},
    {"name": "Marikina",     "region": "NCR", "latitude": 14.6507, "longitude": 121.1029},
    {"name": "Muntinlupa",   "region": "NCR", "latitude": 14.4081, "longitude": 121.0415},
    {"name": "Navotas",      "region": "NCR", "latitude": 14.6667, "longitude": 120.9417},
    {"name": "Parañaque",    "region": "NCR", "latitude": 14.4793, "longitude": 121.0198},
    {"name": "Pasay",        "region": "NCR", "latitude": 14.5378, "longitude": 121.0014},
    {"name": "Pasig",        "region": "NCR", "latitude": 14.5764, "longitude": 121.0851},
    {"name": "Pateros",      "region": "NCR", "latitude": 14.5411, "longitude": 121.0687},
    {"name": "San Juan",     "region": "NCR", "latitude": 14.6019, "longitude": 121.0355},
    {"name": "Taguig",       "region": "NCR", "latitude": 14.5176, "longitude": 121.0509},
    {"name": "Valenzuela",   "region": "NCR", "latitude": 14.7011, "longitude": 120.9830},

    # CAR - Cordillera Administrative Region
    {"name": "Baguio",        "region": "CAR", "latitude": 16.4023, "longitude": 120.5960},
    {"name": "Tabuk",         "region": "CAR", "latitude": 17.4083, "longitude": 121.4453},
    {"name": "La Trinidad",   "region": "CAR", "latitude": 16.4550, "longitude": 120.5883},

    # Region I - Ilocos Region
    {"name": "Laoag",              "region": "Region I", "latitude": 18.1978, "longitude": 120.5936},
    {"name": "Vigan",               "region": "Region I", "latitude": 17.5747, "longitude": 120.3869},
    {"name": "San Fernando (La Union)", "region": "Region I", "latitude": 16.6159, "longitude": 120.3209},
    {"name": "Dagupan",             "region": "Region I", "latitude": 16.0431, "longitude": 120.3331},
    {"name": "Alaminos",            "region": "Region I", "latitude": 16.1556, "longitude": 119.9819},
    {"name": "Candon",              "region": "Region I", "latitude": 17.1948, "longitude": 120.4514},
    {"name": "Batac",               "region": "Region I", "latitude": 18.0594, "longitude": 120.5644},

    # Region II - Cagayan Valley
    {"name": "Tuguegarao", "region": "Region II", "latitude": 17.6132, "longitude": 121.7270},
    {"name": "Ilagan",     "region": "Region II", "latitude": 17.1500, "longitude": 121.8889},
    {"name": "Cauayan",    "region": "Region II", "latitude": 16.9333, "longitude": 121.7667},
    {"name": "Santiago",   "region": "Region II", "latitude": 16.6889, "longitude": 121.5486},

    # Region III - Central Luzon
    {"name": "San Fernando (Pampanga)", "region": "Region III", "latitude": 15.0286, "longitude": 120.6898},
    {"name": "Angeles",                 "region": "Region III", "latitude": 15.1450, "longitude": 120.5931},
    {"name": "Olongapo",                "region": "Region III", "latitude": 14.8294, "longitude": 120.2828},
    {"name": "Balanga",                 "region": "Region III", "latitude": 14.6761, "longitude": 120.5361},
    {"name": "Malolos",                 "region": "Region III", "latitude": 14.8433, "longitude": 120.8114},
    {"name": "Meycauayan",              "region": "Region III", "latitude": 14.7358, "longitude": 120.9583},
    {"name": "San Jose del Monte",      "region": "Region III", "latitude": 14.8136, "longitude": 121.0453},
    {"name": "Cabanatuan",              "region": "Region III", "latitude": 15.4864, "longitude": 120.9686},
    {"name": "Gapan",                   "region": "Region III", "latitude": 15.3061, "longitude": 120.9481},
    {"name": "Palayan",                 "region": "Region III", "latitude": 15.5378, "longitude": 121.0817},
    {"name": "Tarlac City",             "region": "Region III", "latitude": 15.4755, "longitude": 120.5960},

    # Region IV-A - CALABARZON
    {"name": "Batangas City", "region": "Region IV-A", "latitude": 13.7565, "longitude": 121.0583},
    {"name": "Lipa",          "region": "Region IV-A", "latitude": 13.9411, "longitude": 121.1622},
    {"name": "Tanauan",       "region": "Region IV-A", "latitude": 14.0864, "longitude": 121.1497},
    {"name": "Calamba",       "region": "Region IV-A", "latitude": 14.2117, "longitude": 121.1653},
    {"name": "Santa Rosa",    "region": "Region IV-A", "latitude": 14.3122, "longitude": 121.1114},
    {"name": "San Pablo",     "region": "Region IV-A", "latitude": 14.0683, "longitude": 121.3256},
    {"name": "Antipolo",      "region": "Region IV-A", "latitude": 14.5878, "longitude": 121.1760},
    {"name": "Lucena",        "region": "Region IV-A", "latitude": 13.9373, "longitude": 121.6170},
    {"name": "Cavite City",   "region": "Region IV-A", "latitude": 14.4791, "longitude": 120.8970},
    {"name": "Bacoor",        "region": "Region IV-A", "latitude": 14.4597, "longitude": 120.9367},
    {"name": "Dasmariñas",    "region": "Region IV-A", "latitude": 14.3294, "longitude": 120.9367},
    {"name": "Imus",          "region": "Region IV-A", "latitude": 14.4297, "longitude": 120.9367},
    {"name": "Trece Martires","region": "Region IV-A", "latitude": 14.2825, "longitude": 120.8681},
    {"name": "Tagaytay",      "region": "Region IV-A", "latitude": 14.1153, "longitude": 120.9621},

    # MIMAROPA
    {"name": "Calapan",         "region": "MIMAROPA", "latitude": 13.4115, "longitude": 121.1803},
    {"name": "Puerto Princesa", "region": "MIMAROPA", "latitude": 9.7392,  "longitude": 118.7353},
    {"name": "Odiongan",        "region": "MIMAROPA", "latitude": 12.4033, "longitude": 121.9908},
    {"name": "Boac",            "region": "MIMAROPA", "latitude": 13.4453, "longitude": 121.8386},

    # Region V - Bicol Region
    {"name": "Legazpi",       "region": "Region V", "latitude": 13.1391, "longitude": 123.7438},
    {"name": "Naga",          "region": "Region V", "latitude": 13.6218, "longitude": 123.1948},
    {"name": "Iriga",         "region": "Region V", "latitude": 13.4272, "longitude": 123.4131},
    {"name": "Sorsogon City", "region": "Region V", "latitude": 12.9742, "longitude": 124.0058},
    {"name": "Masbate City",  "region": "Region V", "latitude": 12.3686, "longitude": 123.6222},
    {"name": "Tabaco",        "region": "Region V", "latitude": 13.3572, "longitude": 123.7328},
    {"name": "Ligao",         "region": "Region V", "latitude": 13.2333, "longitude": 123.5333},
    {"name": "Daet",          "region": "Region V", "latitude": 14.1122, "longitude": 122.9550},

    # Region VI - Western Visayas
    {"name": "Iloilo",  "region": "Region VI", "latitude": 10.7202, "longitude": 122.5621},
    {"name": "Bacolod",  "region": "Region VI", "latitude": 10.6765, "longitude": 122.9509},
    {"name": "Roxas",    "region": "Region VI", "latitude": 11.5853, "longitude": 122.7511},
    {"name": "Kalibo",   "region": "Region VI", "latitude": 11.7079, "longitude": 122.3647},
    {"name": "San Carlos (Negros Occidental)", "region": "Region VI", "latitude": 10.4926, "longitude": 123.4162},
    {"name": "Silay",    "region": "Region VI", "latitude": 10.7981, "longitude": 122.9738},
    {"name": "Bago",     "region": "Region VI", "latitude": 10.5333, "longitude": 122.8333},
    {"name": "Talisay (Negros Occidental)", "region": "Region VI", "latitude": 10.7373, "longitude": 122.9647},

    # Region VII - Central Visayas
    {"name": "Cebu",       "region": "Region VII", "latitude": 10.3157, "longitude": 123.8854},
    {"name": "Mandaue",    "region": "Region VII", "latitude": 10.3237, "longitude": 123.9227},
    {"name": "Lapu-Lapu",  "region": "Region VII", "latitude": 10.3103, "longitude": 123.9494},
    {"name": "Tagbilaran", "region": "Region VII", "latitude": 9.6474,  "longitude": 123.8536},
    {"name": "Dumaguete",  "region": "Region VII", "latitude": 9.3103,  "longitude": 123.3080},
    {"name": "Toledo",     "region": "Region VII", "latitude": 10.3775, "longitude": 123.6389},
    {"name": "Danao",      "region": "Region VII", "latitude": 10.5267, "longitude": 124.0264},

    # Region VIII - Eastern Visayas
    {"name": "Tacloban",  "region": "Region VIII", "latitude": 11.2447, "longitude": 125.0048},
    {"name": "Ormoc",     "region": "Region VIII", "latitude": 11.0064, "longitude": 124.6075},
    {"name": "Catbalogan","region": "Region VIII", "latitude": 11.7753, "longitude": 124.8861},
    {"name": "Calbayog",  "region": "Region VIII", "latitude": 12.0667, "longitude": 124.6000},
    {"name": "Maasin",    "region": "Region VIII", "latitude": 10.1333, "longitude": 124.8500},
    {"name": "Borongan",  "region": "Region VIII", "latitude": 11.6083, "longitude": 125.4306},

    # Region IX - Zamboanga Peninsula
    {"name": "Zamboanga City", "region": "Region IX", "latitude": 6.9214, "longitude": 122.0790},
    {"name": "Pagadian",       "region": "Region IX", "latitude": 7.8257, "longitude": 123.4372},
    {"name": "Dipolog",        "region": "Region IX", "latitude": 8.5889, "longitude": 123.3411},
    {"name": "Isabela City",   "region": "Region IX", "latitude": 6.7031, "longitude": 121.9711},

    # Region X - Northern Mindanao
    {"name": "Cagayan de Oro", "region": "Region X", "latitude": 8.4542, "longitude": 124.6319},
    {"name": "Iligan",         "region": "Region X", "latitude": 8.2280, "longitude": 124.2452},
    {"name": "Malaybalay",     "region": "Region X", "latitude": 8.1575, "longitude": 125.1278},
    {"name": "Valencia",       "region": "Region X", "latitude": 7.9061, "longitude": 125.0947},
    {"name": "Ozamiz",         "region": "Region X", "latitude": 8.1500, "longitude": 123.8422},
    {"name": "Gingoog",        "region": "Region X", "latitude": 8.8281, "longitude": 125.1042},

    # Region XI - Davao Region
    {"name": "Davao",  "region": "Region XI", "latitude": 7.1907, "longitude": 125.4553},
    {"name": "Tagum",  "region": "Region XI", "latitude": 7.4478, "longitude": 125.8078},
    {"name": "Panabo", "region": "Region XI", "latitude": 7.3081, "longitude": 125.6844},
    {"name": "Digos",  "region": "Region XI", "latitude": 6.7497, "longitude": 125.3572},
    {"name": "Mati",   "region": "Region XI", "latitude": 6.9497, "longitude": 126.2153},

    # Region XII - SOCCSKSARGEN
    {"name": "Koronadal",       "region": "Region XII", "latitude": 6.5031, "longitude": 124.8467},
    {"name": "General Santos",  "region": "Region XII", "latitude": 6.1164, "longitude": 125.1716},
    {"name": "Kidapawan",       "region": "Region XII", "latitude": 7.0083, "longitude": 125.0894},
    {"name": "Tacurong",        "region": "Region XII", "latitude": 6.6928, "longitude": 124.6753},

    # Region XIII - Caraga
    {"name": "Butuan",  "region": "Region XIII", "latitude": 8.9475, "longitude": 125.5406},
    {"name": "Surigao City", "region": "Region XIII", "latitude": 9.7833, "longitude": 125.4917},
    {"name": "Bislig",  "region": "Region XIII", "latitude": 8.2153, "longitude": 126.3181},
    {"name": "Tandag",  "region": "Region XIII", "latitude": 9.0781, "longitude": 126.1986},
    {"name": "Bayugan", "region": "Region XIII", "latitude": 8.7167, "longitude": 125.7500},

    # BARMM - Bangsamoro Autonomous Region in Muslim Mindanao
    {"name": "Cotabato City", "region": "BARMM", "latitude": 7.2231, "longitude": 124.2452},
    {"name": "Marawi",        "region": "BARMM", "latitude": 8.0000, "longitude": 124.2928},
    {"name": "Lamitan",       "region": "BARMM", "latitude": 6.6547, "longitude": 122.1275},
]

DELAY = 2
MAX_RETRIES = 3

BASE_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_VARS = "temperature_2m,rain,wind_speed_10m"
TIMEZONE = "Asia/Manila"
SOURCE_NAME = "open-meteo"


conn = psycopg2.connect(
    host="postgres_weather",      # or "postgres_weather" if this script itself runs inside Docker
    port=5432,
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
            city["latitude"],
            city["longitude"],
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
 


