import unittest

from inkdaddy_hub.config import HubSettings
from inkdaddy_hub.services.updates import (
    GitHubRelease,
    get_firmware_update_info,
    is_newer_version,
    normalize_github_repo,
    select_firmware_asset,
    select_source_asset,
)


class UpdateServiceTests(unittest.TestCase):
    def release(self) -> GitHubRelease:
        return GitHubRelease.from_api(
            {
                "tag_name": "v0.2.0",
                "name": "v0.2.0",
                "body": "release notes",
                "html_url": "https://github.com/willcrain/inkDaddy/releases/tag/v0.2.0",
                "tarball_url": "https://api.github.com/repos/willcrain/inkDaddy/tarball/v0.2.0",
                "published_at": "2026-06-10T00:00:00Z",
                "prerelease": False,
                "assets": [
                    {
                        "name": "inkdaddy-v0.2.0.tar.gz",
                        "browser_download_url": "https://github.com/example/source.tgz",
                        "digest": "sha256:" + "a" * 64,
                        "size": 123,
                    },
                    {
                        "name": "inkdaddy-firmware-xiao_mg24-v0.2.0.gbl",
                        "browser_download_url": "https://github.com/example/fw.gbl",
                        "digest": "sha256:" + "b" * 64,
                        "size": 456,
                    },
                ],
            }
        )

    def test_normalizes_github_repo_urls(self):
        self.assertEqual(normalize_github_repo("willcrain/inkDaddy"), "willcrain/inkDaddy")
        self.assertEqual(
            normalize_github_repo("https://github.com/willcrain/inkDaddy.git"),
            "willcrain/inkDaddy",
        )
        self.assertEqual(normalize_github_repo("git@github.com:willcrain/inkDaddy.git"), "willcrain/inkDaddy")
        self.assertIsNone(normalize_github_repo("https://github.com/OWNER/inkDaddy.git"))

    def test_compares_release_versions(self):
        self.assertTrue(is_newer_version("v0.2.0", "0.1.9"))
        self.assertFalse(is_newer_version("v0.2.0", "0.2.0"))
        self.assertTrue(is_newer_version("v2026.06.10", "main"))

    def test_selects_release_source_asset(self):
        asset = select_source_asset(self.release())
        self.assertIsNotNone(asset)
        self.assertEqual(asset.sha256, "a" * 64)

    def test_selects_board_firmware_asset(self):
        asset = select_firmware_asset(self.release(), "xiao_mg24")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.sha256, "b" * 64)

    def test_firmware_check_reports_not_configured_without_repo(self):
        info = get_firmware_update_info(
            board="xiao_mg24",
            current_version="0.1.0",
            settings=HubSettings(github_repo=None),
        )
        self.assertEqual(info.status, "not_configured")
        self.assertFalse(info.update_available)


if __name__ == "__main__":
    unittest.main()
