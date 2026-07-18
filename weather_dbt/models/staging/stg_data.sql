SELECT
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