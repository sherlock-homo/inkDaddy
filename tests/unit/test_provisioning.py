import unittest

from inkdaddy_hub.services.provisioning import DisplayContentKind, ProvisioningState, next_display_content_kind


class ProvisioningTests(unittest.TestCase):
    def test_joined_device_shows_normal_frame(self):
        state = ProvisioningState(True, True, 0, 0)
        self.assertEqual(next_display_content_kind(state), DisplayContentKind.NORMAL_FRAME)

    def test_unjoined_without_content_shows_join_screen(self):
        state = ProvisioningState(False, False, 0, 3)
        self.assertEqual(next_display_content_kind(state), DisplayContentKind.MATTER_JOIN_SCREEN)

    def test_unjoined_with_content_alternates(self):
        first = ProvisioningState(False, False, 2, 0)
        second = ProvisioningState(False, False, 2, 1)
        third = ProvisioningState(False, False, 2, 2)
        self.assertEqual(next_display_content_kind(first), DisplayContentKind.MATTER_JOIN_SCREEN)
        self.assertEqual(next_display_content_kind(second), DisplayContentKind.NORMAL_FRAME)
        self.assertEqual(next_display_content_kind(third), DisplayContentKind.MATTER_JOIN_SCREEN)
