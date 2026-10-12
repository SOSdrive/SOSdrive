import asyncio
import threading
import unittest
from unittest.mock import Mock, patch

import requests

from sosdrive import (
    AuthState,
    InvalidCredentialsError,
    XanoAPIError,
    login_with_xano,
)


CONNECTION_ERROR = (
    "Erro ao conectar com o servidor Xano. "
    "Verifique a URL do endpoint ou sua conexão com a internet."
)


def make_auth_state(email: str = "ana@example.com", password: str = "secret"):
    state = AuthState.__new__(AuthState)
    object.__setattr__(state, "dirty_vars", set())
    initial_values = {
        "auth_token": "",
        "user_json": "",
        "user": {},
        "user_id": "",
        "user_role": "cliente",
        "email": email,
        "password": password,
        "error_message": "",
        "is_loading": False,
        "session_validated": False,
        "user_profile_photo": "",
        "selected_profile_image": "",
        "user_full_name": "Usuário SOS",
        "user_email": "usuario@exemplo.com",
        "user_phone": "(11) 99999-9999",
        "user_cpf": "",
        "profile_exists": False,
    }
    for name, value in initial_values.items():
        object.__setattr__(state, name, value)
    return state


def consume_event_generator(generator):
    async def consume():
        return [event async for event in generator]

    return asyncio.run(consume())


class TestXanoLogin(unittest.TestCase):
    def test_login_request_uses_normalized_endpoint_json_and_content_type(self):
        response = Mock(status_code=200)
        response.content = b'{"authToken":"token-123","user_id":7}'
        response.json.return_value = {"authToken": "token-123", "user_id": 7}

        with patch("sosdrive.requests.post", return_value=response) as post:
            result = login_with_xano(
                " ANA@EXAMPLE.COM ",
                "secret",
                " https://xano.example/api/ ",
            )

        self.assertEqual(result, ("token-123", 7))
        post.assert_called_once_with(
            "https://xano.example/api/auth/login",
            headers={"Content-Type": "application/json"},
            json={"email": "ana@example.com", "password": "secret"},
            timeout=10,
        )

    def test_login_accepts_token_and_user_id_aliases(self):
        response = Mock(status_code=200)
        response.content = b'{"token":"token-123","user":{"id":7}}'
        response.json.return_value = {"token": "token-123", "user": {"id": 7}}

        with patch("sosdrive.requests.post", return_value=response):
            self.assertEqual(
                login_with_xano("ana@example.com", "secret", "https://xano.example/api"),
                ("token-123", 7),
            )

    def test_login_rejects_malformed_success_response(self):
        response = Mock(status_code=200)
        response.content = b'{"unexpected":"response"}'
        response.json.return_value = {"unexpected": "response"}

        with patch("sosdrive.requests.post", return_value=response):
            with self.assertRaises(XanoAPIError):
                login_with_xano("ana@example.com", "secret", "https://xano.example/api")

    def test_login_maps_http_400_and_401_to_safe_credential_errors(self):
        for status_code in (400, 401):
            with self.subTest(status_code=status_code):
                response = Mock(status_code=status_code)
                response.content = b'{"message":"Invalid credentials"}'
                response.json.return_value = {"message": "Invalid credentials"}
                with patch("sosdrive.requests.post", return_value=response):
                    with self.assertRaises(InvalidCredentialsError) as error:
                        login_with_xano("ana@example.com", "secret", "https://xano.example/api")
                self.assertEqual(error.exception.message, "Invalid credentials")

    def test_login_routes_client_and_provider_and_keeps_token_in_server_state(self):
        for role, expected_route in (
            ("cliente", "/perfil-cliente"),
            ("prestador", "/perfil-prestador"),
        ):
            with self.subTest(role=role):
                state = make_auth_state()
                with (
                    patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
                    patch("sosdrive.login_with_xano", return_value=("token-123", 7)),
                    patch(
                        "sosdrive.fetch_authenticated_user",
                        return_value={"id": 7, "email": "ana@example.com", "name": "Ana", "role": role},
                    ),
                ):
                    events = consume_event_generator(state.login())

                self.assertEqual(state.auth_token, "token-123")
                self.assertEqual(state.user_id, "7")
                self.assertEqual(state.user_role, role)
                self.assertFalse(state.is_loading)
                self.assertEqual(state.password, "")
                self.assertEqual(len(events), 2)
                self.assertIn(expected_route, repr(events[-1]))
                self.assertEqual(AuthState.__annotations__["auth_token"], "str")

    def test_login_connection_failure_shows_safe_message_and_clears_password(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.login_with_xano",
                side_effect=requests.ConnectionError("private network detail"),
            ),
        ):
            consume_event_generator(state.login())

        self.assertEqual(state.error_message, CONNECTION_ERROR)
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.auth_token, "")

    def test_login_exposes_loading_state_while_xano_request_is_pending(self):
        state = make_auth_state()
        request_started = threading.Event()
        finish_request = threading.Event()

        def delayed_login(email, password, api_url):
            self.assertEqual((email, password, api_url), ("ana@example.com", "secret", "https://xano.example/api"))
            request_started.set()
            if not finish_request.wait(timeout=2):
                raise TimeoutError("test request was not released")
            return "token-123", 7

        async def exercise_loading_state():
            generator = state.login()
            await generator.__anext__()
            request_task = asyncio.create_task(generator.__anext__())
            await asyncio.to_thread(request_started.wait, 1)
            self.assertTrue(state.is_loading)
            finish_request.set()
            await request_task
            self.assertFalse(state.is_loading)

        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch("sosdrive.login_with_xano", side_effect=delayed_login),
            patch(
                "sosdrive.fetch_authenticated_user",
                return_value={"id": 7, "email": "ana@example.com", "role": "cliente"},
            ),
        ):
            asyncio.run(exercise_loading_state())

    def test_login_rejects_missing_api_url_without_sending_credentials(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("sosdrive.login_with_xano") as login_request,
        ):
            consume_event_generator(state.login())

        login_request.assert_not_called()
        self.assertEqual(state.error_message, CONNECTION_ERROR)
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)

    def test_login_rejects_invalid_api_url_without_sending_credentials(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {"XANO_API_URL": "ftp://xano.example/api"}),
            patch("sosdrive.requests.post") as login_request,
        ):
            consume_event_generator(state.login())

        login_request.assert_not_called()
        self.assertEqual(state.error_message, CONNECTION_ERROR)
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)

    def test_login_uses_safe_invalid_credentials_message(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.login_with_xano",
                side_effect=InvalidCredentialsError("E-mail ou senha incorretos."),
            ),
        ):
            consume_event_generator(state.login())

        self.assertEqual(state.error_message, "E-mail ou senha incorretos.")
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.auth_token, "")

    def test_login_does_not_redirect_for_unsupported_role(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch("sosdrive.login_with_xano", return_value=("token-123", 7)),
            patch(
                "sosdrive.fetch_authenticated_user",
                return_value={"id": 7, "email": "ana@example.com", "role": "admin"},
            ),
        ):
            events = consume_event_generator(state.login())

        self.assertEqual(events, [None])
        self.assertEqual(state.error_message, "Sua conta não possui um tipo de usuário válido.")
        self.assertEqual(state.auth_token, "")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.password, "")


if __name__ == "__main__":
    unittest.main()
