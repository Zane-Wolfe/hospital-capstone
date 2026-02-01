import pytest
from unittest.mock import patch


class TestSensorsEndpoints:
    def test_get_sensors_unauthenticated(self, client):
        response = client.get("/api/sensors")
        assert response.status_code == 403

    @patch("app.sensors.service.get_sensors")
    def test_get_sensors_authenticated(self, mock_get_sensors, client, auth_headers):
        mock_get_sensors.return_value = [
            {"sensor_id": "sensor_001", "location": "ICU", "event_count": 150},
            {"sensor_id": "sensor_002", "location": "ER", "event_count": 200},
        ]
        response = client.get("/api/sensors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("app.sensors.service.get_sensor")
    def test_get_sensor_by_id(self, mock_get_sensor, client, auth_headers):
        mock_get_sensor.return_value = {
            "sensor_id": "sensor_001",
            "location": "ICU",
            "event_count": 150,
        }
        response = client.get("/api/sensors/sensor_001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "sensor_001"

    @patch("app.sensors.service.get_sensor")
    def test_get_sensor_not_found(self, mock_get_sensor, client, auth_headers):
        mock_get_sensor.return_value = None
        response = client.get("/api/sensors/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    @patch("app.sensors.service.get_locations")
    def test_get_locations(self, mock_get_locations, client, auth_headers):
        mock_get_locations.return_value = ["ICU", "ER", "OR", "Ward A"]
        response = client.get("/api/sensors/locations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "ICU" in data


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
