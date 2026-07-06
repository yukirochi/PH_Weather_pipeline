CREATE TABLE IF NOT EXISTS raw.weather_observations (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name           TEXT,
    latitude            NUMERIC(9,6) NOT NULL,
    longitude           NUMERIC(9,6) NOT NULL,
    observed_at         TIMESTAMPTZ NOT NULL,
    temperature_c       NUMERIC(5,2),
    precipitation_mm    NUMERIC(6,2),
    wind_speed_kmh      NUMERIC(5,2),
    raw_payload         JSONB,
    source_name         TEXT        NOT NULL DEFAULT 'open-meteo',
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    batch_id            UUID,
    CONSTRAINT uq_weather_obs UNIQUE (latitude, longitude, observed_at, source_name)
);