SELECT
    city_name,
    COUNT(*) AS row_count,
    MIN(observed_at) AS earliest,
    MAX(observed_at) AS latest,
    MIN(temperature_c) AS min_temp,
    MAX(temperature_c) AS max_temp
FROM raw.weather_observations
GROUP BY city_name
ORDER BY city_name