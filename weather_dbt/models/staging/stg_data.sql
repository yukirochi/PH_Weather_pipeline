WITH staged AS (SELECT
    id,
    latitude,
    longitude,
    city_name,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh,
    EXTRACT(HOUR FROM observed_at) AS observed_hour,
    DATE(observed_at) AS observed_date
FROM raw.weather_observations
WHERE city_name IS NOT NULL
)

-- Select all rows from  staged'
SELECT 
    MAX(id) AS id,
    MAX(latitude) AS latitude,
    MAX(longitude) AS longitude,
    city_name,
    MAX(temperature_c) AS temperature_c,
    MAX(precipitation_mm) AS precipitation_mm,
    MAX(wind_speed_kmh) AS wind_speed_kmh,
    observed_hour,
    MAX(observed_date) AS observed_date
FROM staged 
GROUP BY city_name, observed_hour, observed_date
