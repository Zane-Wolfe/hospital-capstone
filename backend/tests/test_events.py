import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestEventsEndpoints:
    def test_get_events_unauthenticated(self, client):
        response = client.get("/api/events")
        assert response.status_code == 403

    @patch("app.events.service.get_events")
    def test_get_events_authenticated(self, mock_get_events, client, auth_headers, sample_events_list):
        mock_get_events.return_value = sample_events_list
        response = client.get("/api/events", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.events.service.get_events")
    def test_get_events_with_filters(self, mock_get_events, client, auth_headers):
        mock_get_events.return_value = []
        response = client.get(
            "/api/events",
            headers=auth_headers,
            params={
                "time_range": "-1h",
                "location": "ICU",
                "event_type": "alarm",
            },
        )
        assert response.status_code == 200
        mock_get_events.assert_called_once()

    @patch("app.events.service.get_latest_events")
    def test_get_latest_events(self, mock_get_latest, client, auth_headers, sample_events_list):
        mock_get_latest.return_value = sample_events_list[:2]
        response = client.get("/api/events/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.events.service.get_latest_events")
    def test_get_latest_events_with_limit(self, mock_get_latest, client, auth_headers):
        mock_get_latest.return_value = []
        response = client.get(
            "/api/events/latest",
            headers=auth_headers,
            params={"limit": 5},
        )
        assert response.status_code == 200
        mock_get_latest.assert_called_once_with(5)

    @patch("app.events.service.get_event_stats")
    def test_get_event_stats(self, mock_get_stats, client, auth_headers):
        mock_get_stats.return_value = {
            "total_events": 100,
            "avg_loudness": 65.5,
            "avg_confidence": 0.88,
            "event_types": {"alarm": 30, "speech": 50, "cough": 20},
        }
        response = client.get("/api/events/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "avg_loudness" in data
        assert "event_types" in data

    @patch("app.events.service.get_loudness_timeseries")
    def test_get_loudness_timeseries(self, mock_get_ts, client, auth_headers):
        mock_get_ts.return_value = [
            {"time": "2024-01-15T10:00:00Z", "value": 65.0},
            {"time": "2024-01-15T10:05:00Z", "value": 70.0},
        ]
        response = client.get("/api/events/timeseries/loudness", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.events.service.get_event_count_timeseries")
    def test_get_event_count_timeseries(self, mock_get_ts, client, auth_headers):
        mock_get_ts.return_value = [
            {"time": "2024-01-15T10:00:00Z", "value": 5},
            {"time": "2024-01-15T10:05:00Z", "value": 8},
        ]
        response = client.get("/api/events/timeseries/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.events.service.get_confidence_timeseries")
    def test_get_confidence_timeseries(self, mock_get_ts, client, auth_headers):
        mock_get_ts.return_value = [
            {"time": "2024-01-15T10:00:00Z", "value": 0.85},
            {"time": "2024-01-15T10:05:00Z", "value": 0.90},
        ]
        response = client.get("/api/events/timeseries/confidence", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.events.service.get_heatmap_data")
    def test_get_heatmap_data(self, mock_get_heatmap, client, auth_headers):
        mock_get_heatmap.return_value = [
            {"location": "ICU", "count": 45, "avg_loudness": 68.0},
            {"location": "ER", "count": 30, "avg_loudness": 72.0},
        ]
        response = client.get("/api/events/heatmap", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
