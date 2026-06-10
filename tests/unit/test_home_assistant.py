import unittest

from inkdaddy_hub.services.home_assistant import normalize_state_response, profile_token_url, safe_ha_log_payload


class HomeAssistantTests(unittest.TestCase):
    def test_normalizes_states(self):
        entities = normalize_state_response(
            [
                {
                    "entity_id": "sensor.temp",
                    "state": "72",
                    "attributes": {"friendly_name": "Temperature"},
                }
            ]
        )
        self.assertEqual(entities[0].domain, "sensor")
        self.assertEqual(entities[0].name, "Temperature")

    def test_profile_url(self):
        self.assertEqual(profile_token_url("http://homeassistant.local:8123/"), "http://homeassistant.local:8123/profile")

    def test_redacts_token(self):
        payload = safe_ha_log_payload({"token": "abcdef123456", "nested": {"password": "supersecret"}})
        self.assertIn("<redacted>", payload["token"])
        self.assertEqual(payload["nested"]["password"], "su<redacted>et")
