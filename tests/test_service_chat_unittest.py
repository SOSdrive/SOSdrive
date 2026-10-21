import asyncio
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import requests

from sosdrive import (
    OperationalState,
    XanoAPIError,
    accept_service_request_xano,
    client_message_panel,
    customer_dashboard,
    provider_service_progress_screen,
    release_service_request_xano,
    service_message_panel,
)


def walk_components(component):
    yield component
    for child in getattr(component, "children", ()):
        if hasattr(child, "children"):
            yield from walk_components(child)


class TestServiceChat(unittest.TestCase):
    def test_xano_provider_guards_allow_only_the_assigned_provider(self):
        xano_root = Path(__file__).resolve().parents[1] / "xano" / "api" / "service_requests"
        accept_script = (xano_root / "accept" / "accept_POST.xs").read_text()
        release_script = (xano_root / "update_request_status" / "update_request_status_POST.xs").read_text()
        complete_script = (xano_root / "status" / "status_PATCH.xs").read_text()

        self.assertIn(
            'precondition ($authenticated_user.role == "prestador")',
            accept_script,
        )
        assigned_provider_guard = (
            'precondition ($existing_request.provider_id == $auth.id '
            '&& $authenticated_user.role == "prestador")'
        )
        self.assertIn(assigned_provider_guard, release_script)
        self.assertIn(assigned_provider_guard, complete_script)

    def test_xano_acceptance_uses_unique_request_claim_before_assignment(self):
        xano_root = Path(__file__).resolve().parents[1] / "xano"
        acceptance_table = (xano_root / "table" / "service_request_acceptance.xs").read_text()
        accept_script = (
            xano_root / "api" / "service_requests" / "accept" / "accept_POST.xs"
        ).read_text()

        self.assertIn(
            '{type: "btree|unique", field: [{name: "service_request_id"}]}',
            acceptance_table,
        )
        self.assertLess(
            accept_script.index("db.add service_request_acceptance"),
            accept_script.index("db.edit service_request"),
        )

    def make_state(self, *, provider_panel=False, client_panel=False, request_id=42):
        state = OperationalState.__new__(OperationalState)
        values = {
            "dirty_vars": set(),
            "atendimento_mock": {"id": request_id} if provider_panel else {},
            "request_id": request_id if client_panel else None,
            "show_message_panel": provider_panel,
            "show_client_message_panel": client_panel,
            "active_message_request_id": request_id,
            "message_poll_generation": 1,
            "message_sync_status": "",
            "service_messages": [{"id": 1, "message_text": "old"}],
        }
        for key, value in values.items():
            object.__setattr__(state, key, value)
        return state

    def test_accept_request_uses_authenticated_accept_endpoint(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 42, "status": "accepted", "provider_id": 7}

        with patch("sosdrive.requests.post", return_value=response) as post:
            result = accept_service_request_xano(
                "provider-token",
                "https://xano.example/api:services",
                42,
            )

        self.assertEqual(result["provider_id"], 7)
        post.assert_called_once_with(
            "https://xano.example/api:services/42/accept",
            headers={"Authorization": "Bearer provider-token"},
            timeout=10,
        )

    def test_releasing_request_uses_only_the_pending_transition(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 42, "status": "pending", "provider_id": None}

        with patch("sosdrive.requests.post", return_value=response) as post:
            release_service_request_xano(
                "provider-token",
                "https://xano.example/api:services",
                42,
            )

        post.assert_called_once_with(
            "https://xano.example/api:services/update_request_status",
            json={"request_id": 42, "status": "pending"},
            headers={"Authorization": "Bearer provider-token"},
            timeout=10,
        )

    def test_provider_conversation_refresh_replaces_messages_without_duplicates(self):
        state = self.make_state(provider_panel=True)
        refreshed = [
            {"id": 1, "message_text": "old"},
            {"id": 2, "message_text": "new from client"},
        ]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="provider-token"),
            ),
            patch("sosdrive.get_xano_services_url", return_value="https://xano.example/api:services"),
            patch("sosdrive.fetch_service_messages_xano", return_value=refreshed) as fetch,
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertTrue(result)
        self.assertEqual(state.service_messages, refreshed)
        self.assertEqual([message["id"] for message in state.service_messages], [1, 2])
        self.assertEqual(state.message_sync_status, "Atualização automática ativa.")
        fetch.assert_called_once_with("provider-token", "https://xano.example/api:services", 42)

    def test_client_conversation_refreshes_its_active_request(self):
        state = self.make_state(provider_panel=False, client_panel=True)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="client-token"),
            ),
            patch("sosdrive.get_xano_services_url", return_value="https://xano.example/api:services"),
            patch(
                "sosdrive.fetch_service_messages_xano",
                return_value=[{"id": 2, "message_text": "reply from provider"}],
            ) as fetch,
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertTrue(result)
        self.assertEqual(state.service_messages[0]["message_text"], "reply from provider")
        fetch.assert_called_once_with("client-token", "https://xano.example/api:services", 42)

    def test_refresh_failure_preserves_messages_and_reports_retry(self):
        state = self.make_state(provider_panel=True)
        existing_messages = list(state.service_messages)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="provider-token"),
            ),
            patch("sosdrive.get_xano_services_url", return_value="https://xano.example/api:services"),
            patch(
                "sosdrive.fetch_service_messages_xano",
                side_effect=requests.ConnectionError("private network detail"),
            ),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertFalse(result)
        self.assertEqual(state.service_messages, existing_messages)
        self.assertIn("Tentando novamente", state.message_sync_status)
        self.assertNotIn("private network detail", "\n".join(captured.output))

    def test_closed_or_changed_conversation_is_not_refreshed(self):
        state = self.make_state(provider_panel=True)
        state.show_message_panel = False

        with patch("sosdrive.fetch_service_messages_xano") as fetch:
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertFalse(result)
        fetch.assert_not_called()

    def test_closing_provider_conversation_invalidates_its_poll_loop(self):
        state = self.make_state(provider_panel=True)
        generation = state.message_poll_generation

        state.close_message_panel()

        self.assertFalse(state.show_message_panel)
        self.assertIsNone(state.active_message_request_id)
        self.assertEqual(state.message_poll_generation, generation + 1)

    def test_background_poll_runs_every_two_seconds_and_stops_on_close(self):
        state = self.make_state(provider_panel=True)
        delays = []

        async def sleep_and_close_after_one_refresh(delay):
            delays.append(delay)
            if len(delays) == 2:
                state.close_message_panel()

        async def run_poll():
            with (
                patch("sosdrive.asyncio.sleep", new=sleep_and_close_after_one_refresh),
                patch.object(
                    OperationalState,
                    "_get_auth_token",
                    new=AsyncMock(return_value="provider-token"),
                ),
                patch("sosdrive.get_xano_services_url", return_value="https://xano.example/api:services"),
                patch("sosdrive.fetch_service_messages_xano", return_value=[]) as fetch,
            ):
                await OperationalState.poll_service_messages.fn(state)
            return fetch

        fetch = asyncio.run(run_poll())

        self.assertEqual(delays, [2, 2])
        self.assertEqual(fetch.call_count, 1)
        self.assertFalse(state.show_message_panel)

    def test_provider_and_client_chat_buttons_start_their_polling_loop(self):
        cases = (
            (provider_service_progress_screen(), "open_message_panel"),
            (customer_dashboard(), "open_client_message_panel"),
        )

        for screen, open_handler in cases:
            with self.subTest(open_handler=open_handler):
                event_chains = []
                for component in walk_components(screen):
                    trigger = component.event_triggers.get("on_click")
                    event_names = [
                        event.handler.fn.__name__
                        for event in getattr(trigger, "events", ())
                    ]
                    if open_handler in event_names:
                        event_chains.append(event_names)
                self.assertEqual(len(event_chains), 1)
                self.assertEqual(
                    event_chains[0],
                    [open_handler, "poll_service_messages"],
                )

    def test_both_chat_panels_build_with_accessible_sync_status(self):
        for panel in (service_message_panel(), client_message_panel()):
            components = list(walk_components(panel))
            status_regions = [
                component
                for component in components
                if getattr(component, "tag", None) == "Text"
                and getattr(getattr(component, "role", None), "_var_value", None) == "status"
            ]
            self.assertEqual(len(status_regions), 1)
            self.assertEqual(status_regions[0].custom_attrs.get("aria-live"), "polite")
            self.assertTrue(any(getattr(component, "tag", None) == "Button" for component in components))


if __name__ == "__main__":
    unittest.main()
