import importlib.util
import io
import unittest


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "FastAPI not installed")
class ApiContractTests(unittest.TestCase):
    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app

        client = TestClient(app)
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_simulator_manifest_alternates_join_screen(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app

        client = TestClient(app)
        client.post("/api/simulator/devices", json={"device_uid": "sim-test"})
        first = client.get("/api/devices/sim-test/frame-manifest?refresh_count=0").json()
        second = client.get("/api/devices/sim-test/frame-manifest?refresh_count=1").json()
        self.assertEqual(first["content_kind"], "matter_join_screen")
        self.assertEqual(second["content_kind"], "normal_frame")

    def test_update_api_reports_not_configured_without_repo(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app

        client = TestClient(app)
        response = client.get("/api/updates/hub/check")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["status"], {"not_configured", "error", "current", "update_available"})

        firmware = client.get("/api/updates/firmware/manifest?board=xiao_mg24").json()
        self.assertEqual(firmware["board"], "xiao_mg24")
        self.assertIn("safe_update_required", firmware)

    def test_photo_upload_album_and_frame(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app
        from PIL import Image

        client = TestClient(app)
        image_file = io.BytesIO()
        Image.new("RGB", (64, 32), (255, 0, 0)).save(image_file, format="PNG")
        image_file.seek(0)

        response = client.post(
            "/api/photos/batch",
            files={"files": ("sample.png", image_file, "image/png")},
            data={"mode": "fit"},
        )
        self.assertEqual(response.status_code, 200)
        photo = response.json()["photos"][0]
        self.assertEqual(photo["processed_status"], "ready")
        self.assertEqual(client.get(photo["preview_url"]).status_code, 200)
        self.assertEqual(client.get(photo["frame_url"]).status_code, 200)

        album = client.post("/api/albums", json={"name": "Test album", "photo_ids": [photo["id"]]}).json()
        self.assertEqual(album["item_count"], 1)

    def test_integrations_and_ha_mock_cache(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app

        client = TestClient(app)
        client.post("/api/home-assistant/mock/entities")
        entities = client.get("/api/home-assistant/entities?search=temperature").json()
        self.assertEqual(entities["entities"][0]["entity_id"], "sensor.living_room_temperature")

        integrations = client.get("/api/integrations").json()["integrations"]
        self.assertTrue(any(item["id"] == "home_assistant" for item in integrations))

    def test_device_registry_history_and_frame(self):
        from fastapi.testclient import TestClient
        from inkdaddy_hub.main import app

        client = TestClient(app)
        response = client.post("/api/devices", json={"device_uid": "display-api-test", "name": "API Test"})
        self.assertEqual(response.status_code, 200)
        heartbeat = client.post(
            "/api/devices/display-api-test/heartbeat",
            json={"battery_percent": 90, "battery_voltage": 3.9, "status": "awake"},
        ).json()
        self.assertTrue(heartbeat["ok"])
        self.assertEqual(client.get("/api/devices/display-api-test/history").json()["history"][0]["status"], "awake")
        manifest = client.get("/api/devices/display-api-test/frame-manifest?refresh_count=0").json()
        self.assertIn("frame_id", manifest)
        self.assertEqual(client.get("/api/devices/display-api-test/frame").status_code, 200)
