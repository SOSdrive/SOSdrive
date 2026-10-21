from concurrent.futures import ThreadPoolExecutor
import os
import unittest
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


XANO_TEST_SETTINGS = (
    "XANO_TEST_DISPOSABLE_WORKSPACE",
    "XANO_TEST_API_URL",
    "XANO_TEST_REQUEST_ID",
    "XANO_TEST_CLIENT_TOKEN",
    "XANO_TEST_PROVIDER_TOKEN",
    "XANO_TEST_SECOND_PROVIDER_TOKEN",
    "XANO_TEST_NONPARTICIPANT_TOKEN",
)


@unittest.skipUnless(
    all(os.getenv(setting) for setting in XANO_TEST_SETTINGS)
    and os.getenv("XANO_TEST_DISPOSABLE_WORKSPACE", "").strip().lower() == "true",
    "requires an explicitly configured disposable Xano test workspace and users",
)
class TestServiceChatXanoIntegration(unittest.TestCase):
    def setUp(self):
        if os.getenv("XANO_TEST_DISPOSABLE_WORKSPACE", "").strip().lower() != "true":
            self.fail("Set XANO_TEST_DISPOSABLE_WORKSPACE=true only for a disposable workspace")
        self.api_url = os.environ["XANO_TEST_API_URL"].rstrip("/")
        self.request_id = int(os.environ["XANO_TEST_REQUEST_ID"])
        self.client_token = os.environ["XANO_TEST_CLIENT_TOKEN"]
        self.provider_token = os.environ["XANO_TEST_PROVIDER_TOKEN"]
        self.second_provider_token = os.environ["XANO_TEST_SECOND_PROVIDER_TOKEN"]
        self.nonparticipant_token = os.environ["XANO_TEST_NONPARTICIPANT_TOKEN"]

    def auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_assignment_and_chat_are_restricted_to_request_participants(self):
        base_url = f"{self.api_url}/{self.request_id}"
        accepted_provider_tokens = []
        message_marker = f"xano-chat-integration-{uuid.uuid4()}"

        client_acceptance = requests.post(
            f"{base_url}/accept",
            headers=self.auth_headers(self.client_token),
            timeout=10,
        )
        self.assertGreaterEqual(client_acceptance.status_code, 400)

        provider_tokens = (self.provider_token, self.second_provider_token)
        with ThreadPoolExecutor(max_workers=2) as executor:
            acceptances = list(
                executor.map(
                    lambda token: requests.post(
                        f"{base_url}/accept",
                        headers=self.auth_headers(token),
                        timeout=10,
                    ),
                    provider_tokens,
                )
            )
        successful_indexes = [
            index
            for index, response in enumerate(acceptances)
            if response.status_code in {200, 201}
        ]
        accepted_provider_tokens.extend(
            provider_tokens[index] for index in successful_indexes
        )

        try:
            self.assertEqual(len(successful_indexes), 1)
            winning_token = provider_tokens[successful_indexes[0]]

            provider_message = requests.post(
                f"{base_url}/messages",
                json={"message_text": f"{message_marker}-provider"},
                headers=self.auth_headers(winning_token),
                timeout=10,
            )
            self.assertIn(provider_message.status_code, {200, 201})

            client_message = requests.post(
                f"{base_url}/messages",
                json={"message_text": f"{message_marker}-client"},
                headers=self.auth_headers(self.client_token),
                timeout=10,
            )
            self.assertIn(client_message.status_code, {200, 201})

            for token in (self.client_token, winning_token):
                conversation = requests.get(
                    f"{base_url}/messages",
                    headers=self.auth_headers(token),
                    timeout=10,
                )
                self.assertEqual(conversation.status_code, 200)
                messages = conversation.json()
                self.assertTrue(
                    any(
                        message.get("message_text") == f"{message_marker}-provider"
                        for message in messages
                    )
                )
                self.assertTrue(
                    any(
                        message.get("message_text") == f"{message_marker}-client"
                        for message in messages
                    )
                )

            for method, payload in (
                ("get", None),
                ("post", {"message_text": f"{message_marker}-unauthorized"}),
            ):
                response = getattr(requests, method)(
                    f"{base_url}/messages",
                    headers=self.auth_headers(self.nonparticipant_token),
                    json=payload,
                    timeout=10,
                )
                self.assertGreaterEqual(response.status_code, 400)

            release = requests.post(
                f"{self.api_url}/update_request_status",
                json={"request_id": self.request_id, "status": "pending"},
                headers=self.auth_headers(winning_token),
                timeout=10,
            )
            self.assertLess(release.status_code, 400)
            accepted_provider_tokens.remove(winning_token)

            next_provider_token = provider_tokens[1 - successful_indexes[0]]
            reassignment = requests.post(
                f"{base_url}/accept",
                headers=self.auth_headers(next_provider_token),
                timeout=10,
            )
            self.assertIn(reassignment.status_code, {200, 201})
            accepted_provider_tokens.append(next_provider_token)

            reassigned_conversation = requests.get(
                f"{base_url}/messages",
                headers=self.auth_headers(next_provider_token),
                timeout=10,
            )
            self.assertEqual(reassigned_conversation.status_code, 200)
            self.assertTrue(
                any(
                    message.get("message_text") == f"{message_marker}-client"
                    for message in reassigned_conversation.json()
                )
            )
        finally:
            if accepted_provider_tokens:
                released = False
                for token in accepted_provider_tokens:
                    release = requests.post(
                        f"{self.api_url}/update_request_status",
                        json={"request_id": self.request_id, "status": "pending"},
                        headers=self.auth_headers(token),
                        timeout=10,
                    )
                    if release.status_code < 400:
                        released = True
                        break
                self.assertTrue(
                    released, "Could not release the disposable request after the test"
                )


if __name__ == "__main__":
    unittest.main()
