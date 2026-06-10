import unittest

from inkdaddy_hub.services.dashboard import DashboardValidationError, detect_layout_collisions, validate_dashboard_config


class DashboardValidationTests(unittest.TestCase):
    def test_valid_dashboard(self):
        config = {
            "version": 1,
            "grid": {"cols": 4, "rows": 2},
            "widgets": [
                {"id": "a", "type": "big_number", "x": 0, "y": 0, "w": 1, "h": 1},
                {"id": "b", "type": "line_chart", "x": 1, "y": 0, "w": 2, "h": 1},
                {"id": "c", "type": "text_note", "x": 0, "y": 1, "w": 4, "h": 1},
            ],
        }
        normalized = validate_dashboard_config(config)
        self.assertEqual(normalized["grid"], {"cols": 4, "rows": 2})
        self.assertEqual(len(normalized["widgets"]), 3)

    def test_rejects_overlap(self):
        config = {
            "grid": {"cols": 4, "rows": 2},
            "widgets": [
                {"id": "a", "type": "big_number", "x": 0, "y": 0, "w": 1, "h": 1},
                {"id": "b", "type": "on_off_state", "x": 0, "y": 0, "w": 1, "h": 1},
            ],
        }
        with self.assertRaises(DashboardValidationError):
            validate_dashboard_config(config)

    def test_collision_helper_reports_errors(self):
        errors = detect_layout_collisions(
            [
                {"id": "a", "type": "big_number", "x": 0, "y": 0, "w": 1, "h": 1},
                {"id": "b", "type": "on_off_state", "x": 0, "y": 0, "w": 1, "h": 1},
            ]
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("overlaps", errors[0])

    def test_rejects_invalid_footprint(self):
        with self.assertRaises(DashboardValidationError):
            validate_dashboard_config(
                {
                    "grid": {"cols": 4, "rows": 2},
                    "widgets": [{"id": "bad", "type": "big_number", "x": 0, "y": 0, "w": 4, "h": 2}],
                }
            )
