--
-- PostgreSQL database dump
--

\restrict QDQQjRwPr3LaxqStbS5eocpXLhPvlq1bk9lHMOhs4r39nFbN0bXWIQwdDd4H1A0

-- Dumped from database version 15.18 (Debian 15.18-1.pgdg13+1)
-- Dumped by pg_dump version 15.18 (Debian 15.18-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: raw; Type: SCHEMA; Schema: -; Owner: weather_user
--

CREATE SCHEMA raw;


ALTER SCHEMA raw OWNER TO weather_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: weather_observations; Type: TABLE; Schema: raw; Owner: weather_user
--

CREATE TABLE raw.weather_observations (
    id bigint NOT NULL,
    latitude numeric(9,6) NOT NULL,
    longitude numeric(9,6) NOT NULL,
    observed_at timestamp with time zone NOT NULL,
    temperature_c numeric(5,2),
    precipitation_mm numeric(6,2),
    wind_speed_kmh numeric(5,2),
    raw_payload jsonb,
    source_name text DEFAULT 'open-meteo'::text NOT NULL,
    ingested_at timestamp with time zone DEFAULT now() NOT NULL,
    batch_id uuid,
    city_name text
);


ALTER TABLE raw.weather_observations OWNER TO weather_user;

--
-- Name: weather_observations_id_seq; Type: SEQUENCE; Schema: raw; Owner: weather_user
--

ALTER TABLE raw.weather_observations ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME raw.weather_observations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: weather_observations uq_weather_obs; Type: CONSTRAINT; Schema: raw; Owner: weather_user
--

ALTER TABLE ONLY raw.weather_observations
    ADD CONSTRAINT uq_weather_obs UNIQUE (latitude, longitude, observed_at, source_name);


--
-- Name: weather_observations weather_observations_pkey; Type: CONSTRAINT; Schema: raw; Owner: weather_user
--

ALTER TABLE ONLY raw.weather_observations
    ADD CONSTRAINT weather_observations_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict QDQQjRwPr3LaxqStbS5eocpXLhPvlq1bk9lHMOhs4r39nFbN0bXWIQwdDd4H1A0

