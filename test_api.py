"""
Tests for get_data.py

Run with:
    pytest test_get_data.py -v

Notes:
- get_data.py opens a real psycopg2 connection at import time
  (`conn = psycopg2.connect(...)`). To avoid touching a real DB during
  tests, we patch psycopg2.connect *before* importing the module. The
  `weather_module` fixture below handles this.
"""

import sys
import importlib
from unittest.mock import MagicMock, patch, call

import pytest
import requests


MODULE_NAME = "get_data"  # change if your file has a different name


@pytest.fixture
def weather_module():
    """
    Import (or re-import) the module under test with psycopg2.connect
    mocked out, so importing it never tries to open a real DB connection.
    """
    with patch("psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()

        # Ensure a fresh import so `conn = psycopg2.connect(...)` re-runs
        # against our mock rather than a cached real connection.
        sys.modules.pop(MODULE_NAME, None)
        module = importlib.import_module(MODULE_NAME)

        yield module

        sys.modules.pop(MODULE_NAME, None)


# ---------------------------------------------------------------------------
# build_url
# ---------------------------------------------------------------------------

class TestBuildUrl:
    def test_contains_lat_and_long(self, weather_module):
        city = {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842}
        url = weather_module.build_url(city)
        assert "latitude=14.5995" in url
        assert "longitude=120.9842" in url

    def test_contains_expected_vars_and_timezone(self, weather_module):
        city = {"name": "Cebu", "latitude": 10.3157, "longitude": 123.8854}
        url = weather_module.build_url(city)
        assert "current=temperature_2m,rain,wind_speed_10m" in url
        assert "Asia%2FManila" in url

    def test_starts_with_base_url(self, weather_module):
        city = {"name": "Davao", "latitude": 7.1907, "longitude": 125.4553}
        url = weather_module.build_url(city)
        assert url.startswith(weather_module.BASE_URL)


# ---------------------------------------------------------------------------
# fetch_data
# ---------------------------------------------------------------------------

class TestFetchData:
    def test_success_on_first_try(self, weather_module):
        city = {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842}
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {"current": {"temperature_2m": 30}}

        with patch("requests.get", return_value=fake_response) as mock_get:
            result = weather_module.fetch_data(city)

        assert result == {"current": {"temperature_2m": 30}}
        mock_get.assert_called_once()

    def test_retries_then_succeeds(self, weather_module):
        city = {"name": "Cebu", "latitude": 10.3157, "longitude": 123.8854}
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {"current": {}}

        # Fail twice, succeed on the third attempt
        with patch(
            "requests.get",
            side_effect=[
                requests.RequestException("boom"),
                requests.RequestException("boom again"),
                fake_response,
            ],
        ) as mock_get, patch("get_data.time.sleep") as mock_sleep:
            result = weather_module.fetch_data(city)

        assert result == {"current": {}}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # slept before retries 2 and 3

    def test_returns_none_after_max_retries(self, weather_module):
        city = {"name": "Davao", "latitude": 7.1907, "longitude": 125.4553}

        with patch(
            "requests.get", side_effect=requests.RequestException("down")
        ) as mock_get, patch("get_data.time.sleep") as mock_sleep:
            result = weather_module.fetch_data(city)

        assert result is None
        assert mock_get.call_count == weather_module.MAX_RETRIES
        assert mock_sleep.call_count == weather_module.MAX_RETRIES - 1

    def test_backoff_delays_double_each_time(self, weather_module):
        city = {"name": "Baguio", "latitude": 16.4023, "longitude": 120.5960}

        with patch(
            "requests.get", side_effect=requests.RequestException("down")
        ), patch("get_data.time.sleep") as mock_sleep:
            weather_module.fetch_data(city)

        expected_delays = [
            weather_module.DELAY * (2 ** i)
            for i in range(weather_module.MAX_RETRIES - 1)
        ]
        actual_delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert actual_delays == expected_delays


# ---------------------------------------------------------------------------
# insert_observation
# ---------------------------------------------------------------------------

class TestInsertObservation:
    def test_executes_insert_with_expected_params(self, weather_module):
        city = {"name": "Iloilo", "latitude": 10.7202, "longitude": 122.5621}
        data = {
            "latitude": 10.7202,
            "longitude": 122.5621,
            "current": {
                "time": "2026-07-08T12:00",
                "temperature_2m": 29.5,
                "rain": 0.0,
                "wind_speed_10m": 12.3,
            },
        }
        mock_cursor = MagicMock()

        weather_module.insert_observation(mock_cursor, city, data)

        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]

        assert "INSERT INTO raw.weather_observations" in sql
        assert params[0] == "Iloilo"
        assert params[1] == 10.7202
        assert params[2] == 122.5621
        assert params[3] == "2026-07-08T12:00"
        assert params[4] == 29.5
        assert params[5] == 0.0
        assert params[6] == 12.3
        assert params[8] == weather_module.SOURCE_NAME

    def test_handles_missing_optional_fields_gracefully(self, weather_module):
        city = {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842}
        data = {
            "latitude": 14.5995,
            "longitude": 120.9842,
            "current": {"time": "2026-07-08T12:00"},  # no temp/rain/wind
        }
        mock_cursor = MagicMock()

        weather_module.insert_observation(mock_cursor, city, data)

        _, params = mock_cursor.execute.call_args[0]
        assert params[4] is None  # temperature
        assert params[5] is None  # rain
        assert params[6] is None  # wind


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    def test_skips_city_on_fetch_failure_and_continues(self, weather_module):
        # First city fails, second succeeds
        with patch.object(
            weather_module, "fetch_data", side_effect=[None, {"current": {}}]
        ) as mock_fetch, patch.object(
            weather_module, "insert_observation"
        ) as mock_insert, patch.object(
            weather_module, "CITIES",
            [
                {"name": "A", "latitude": 1, "longitude": 1},
                {"name": "B", "latitude": 2, "longitude": 2},
            ],
        ):
            weather_module.main()

        assert mock_fetch.call_count == 2
        # insert_observation should only be called for the successful city
        assert mock_insert.call_count == 1

    def test_commits_after_each_successful_insert(self, weather_module):
        with patch.object(
            weather_module, "fetch_data", return_value={"current": {}}
        ), patch.object(weather_module, "insert_observation"), patch.object(
            weather_module, "CITIES",
            [{"name": "A", "latitude": 1, "longitude": 1}],
        ):
            weather_module.main()

        weather_module.conn.commit.assert_called_once()

    def test_closes_connection_even_if_error_occurs(self, weather_module):
        with patch.object(
            weather_module, "fetch_data", side_effect=RuntimeError("kaboom")
        ), patch.object(
            weather_module, "CITIES",
            [{"name": "A", "latitude": 1, "longitude": 1}],
        ):
            with pytest.raises(RuntimeError):
                weather_module.main()

        weather_module.conn.close.assert_called_once()