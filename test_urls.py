import os
import unittest

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


class PublishedXanoPathsTest(unittest.TestCase):
    def test_unauthenticated_message_and_status_paths(self):
        base_url = os.getenv("XANO_SERVICES_URL", "").strip().rstrip("/")
        if not base_url:
            self.skipTest("XANO_SERVICES_URL is not configured")

        checks = (
            ("GET", "/1/messages", None, 401),
            ("POST", "/1/messages", {"message_text": "probe"}, 401),
            ("PATCH", "/1/status", {"status": "completed"}, 401),
            ("PATCH", "/1", {"status": "completed"}, 404),
            ("PATCH", "/1/messages", {"status": "completed"}, 404),
        )

        for method, path, payload, expected_status in checks:
            with self.subTest(method=method, path=path):
                response = requests.request(
                    method,
                    f"{base_url}{path}",
                    json=payload,
                    timeout=10,
                )
                self.assertEqual(response.status_code, expected_status)


if __name__ == "__main__":
    unittest.main()
