import base64
import io
import os
import unittest
import zipfile
from unittest.mock import patch

from postovaya.http_app import build_box_archive


class DownloadTests(unittest.TestCase):
    SAMPLE_OVPN = "client\nremote example.com 1194\n"

    def assertArchive(self, platform, expected_script):
        with patch.dict(os.environ, {"VPN_BOX_OVPN_B64": base64.b64encode(self.SAMPLE_OVPN.encode("utf-8")).decode("ascii")}, clear=True):
            name, payload = build_box_archive(platform)

        self.assertEqual(name, f"vpn-box-{platform}.zip")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(set(archive.namelist()), {"README.txt", "vpn-box.ovpn", expected_script})
            self.assertEqual(archive.read("vpn-box.ovpn").decode("utf-8"), self.SAMPLE_OVPN)
            self.assertIn("VPN Box", archive.read("README.txt").decode("utf-8"))

    def test_windows_archive_contains_launcher(self):
        self.assertArchive("windows", "install.bat")

    def test_mac_archive_contains_launcher(self):
        self.assertArchive("mac", "install.command")


if __name__ == "__main__":
    unittest.main()
