import importlib.util
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
