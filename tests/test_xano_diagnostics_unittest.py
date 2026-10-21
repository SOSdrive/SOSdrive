import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import requests

from sosdrive import (
    OperationalState,
    XanoAPIError,
    _load_project_environment,
    get_xano_services_url,
    provider_home_screen,
    send_service_message_xano,
)


class TestXanoServiceDiagnostics(unittest.TestCase):
    def test_provider_home_header_and_map_recenter_action_overlay_the_map(self):
        screen = provider_home_screen()
        header = screen.children[0]

        def find_fixed_buttons(component):
            matches = []
            if (
                getattr(component, "tag", None) == "Button"
                and getattr(component, "position", None) == "fixed"
            ):
                matches.append(component)
            for child in getattr(component, "children", ()):
                if hasattr(child, "children"):
                    matches.extend(find_fixed_buttons(child))
            return matches

        recenter_buttons = find_fixed_buttons(screen)

        self.assertEqual(header.position, "fixed")
        self.assertGreater(int(header.z_index), 1000)
        self.assertEqual(len(recenter_buttons), 1)
        self.assertGreater(int(recenter_buttons[0].z_index), 1000)

    def test_provider_availability_toggle_updates_state_and_matching_provider(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "is_available", True)
        object.__setattr__(state, "current_provider_id", 1)
        object.__setattr__(
            state,
            "providers",
            [{"id": 1, "status": "online"}, {"id": 2, "status": "offline"}],
        )

        state.toggle_provider_status()

        self.assertFalse(state.is_available)
        self.assertEqual(state.providers[0]["status"], "offline")
        self.assertEqual(state.providers[1]["status"], "offline")

        state.toggle_provider_status()

        self.assertTrue(state.is_available)
        self.assertEqual(state.providers[0]["status"], "online")

    def test_project_environment_loads_dotenv_without_overriding_process_values(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / ".env"
            env_file.write_text(
                "SOSDRIVE_TEST_XANO_ENV=loaded-from-file\n"
                "SOSDRIVE_TEST_XANO_EXISTING=from-file\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"SOSDRIVE_TEST_XANO_EXISTING": "from-process"},
                clear=False,
            ):
                os.environ.pop("SOSDRIVE_TEST_XANO_ENV", None)
                self.assertTrue(_load_project_environment(env_file))
                self.assertEqual(
                    os.environ["SOSDRIVE_TEST_XANO_ENV"],
                    "loaded-from-file",
                )
                self.assertEqual(
                    os.environ["SOSDRIVE_TEST_XANO_EXISTING"],
                    "from-process",
                )
                os.environ.pop("SOSDRIVE_TEST_XANO_ENV", None)

    def test_services_url_prefers_service_group_url(self):
        with patch.dict(
            "os.environ",
            {
                "XANO_API_URL": "https://xano.example/api:auth",
                "XANO_SERVICES_URL": "https://xano.example/api:services",
            },
        ):
            self.assertEqual(
                get_xano_services_url(),
                "https://xano.example/api:services",
            )

    def test_services_url_falls_back_when_service_group_url_is_missing_or_blank(self):
        with patch.dict(
            "os.environ",
            {
                "XANO_API_URL": "https://xano.example/api:auth/",
                "XANO_SERVICES_URL": "",
            },
        ):
            self.assertEqual(
                get_xano_services_url(),
                "https://xano.example/api:auth",
            )

        with patch.dict(
            "os.environ",
            {"XANO_API_URL": "https://xano.example/api:auth"},
            clear=True,
        ):
            self.assertEqual(get_xano_services_url(), "https://xano.example/api:auth")

    def test_message_text_and_token_are_not_logged_on_success(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 42, "message_text": "private conversation"}
        with (
            patch("sosdrive.requests.post", return_value=response) as post,
            self.assertLogs("sosdrive", level="INFO") as captured,
        ):
            result = send_service_message_xano(
                "secret-auth-token",
                "https://xano.example/api:services",
                42,
                "private conversation",
            )

        self.assertEqual(result["id"], 42)
        post.assert_called_once()
        log_output = "\n".join(captured.output)
        self.assertIn("/42/messages", log_output)
        self.assertNotIn("private conversation", log_output)
        self.assertNotIn("secret-auth-token", log_output)

    def test_message_failure_logs_status_without_response_body_or_message(self):
        response = Mock(status_code=500)
        with (
            patch("sosdrive.requests.post", return_value=response),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            with self.assertRaisesRegex(XanoAPIError, "Service message request failed"):
                send_service_message_xano(
                    "secret-auth-token",
                    "https://xano.example/api:services",
                    42,
                    "private conversation",
                )

        log_output = "\n".join(captured.output)
        self.assertIn("status=500", log_output)
        self.assertNotIn("private conversation", log_output)
        self.assertNotIn("secret-auth-token", log_output)

    def test_message_handler_does_not_log_raw_network_exception(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "message_draft", "private conversation")
        object.__setattr__(state, "atendimento_mock", {"id": 42})
        object.__setattr__(state, "message_error", "")
        object.__setattr__(state, "service_messages", [])
        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="secret-auth-token"),
            ),
            patch(
                "sosdrive.send_service_message_xano",
                side_effect=requests.ConnectionError("private network detail"),
            ),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            asyncio.run(state.send_message())

        log_output = "\n".join(captured.output)
        self.assertIn("ConnectionError", log_output)
        self.assertNotIn("private conversation", log_output)
        self.assertNotIn("secret-auth-token", log_output)
        self.assertNotIn("private network detail", log_output)


if __name__ == "__main__":
    unittest.main()
