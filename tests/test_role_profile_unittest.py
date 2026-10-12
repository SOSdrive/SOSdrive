import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from sosdrive import (
    AuthState,
    OperationalState,
    UnsupportedRoleError,
    _is_duplicate_email_error,
    build_image_data_url,
    fetch_user_profile,
    format_cpf,
    format_phone,
    normalize_user_role,
    pending_provider_requests,
    save_user_profile,
    upload_user_profile_photo,
    validate_signup,
)


class TestRoleProfile(unittest.TestCase):
    def test_normalize_user_role_supports_canonical_and_legacy_values(self):
        self.assertEqual(normalize_user_role("cliente"), "cliente")
        self.assertEqual(normalize_user_role("prestador"), "prestador")
        self.assertEqual(normalize_user_role("client"), "cliente")
        self.assertEqual(normalize_user_role("provider"), "prestador")

    def test_normalize_user_role_rejects_unknown_values(self):
        with self.assertRaises(UnsupportedRoleError):
            normalize_user_role("admin")

    def test_profile_masks_keep_expected_display_format(self):
        self.assertEqual(format_cpf("12345678901"), "123.456.789-01")
        self.assertEqual(format_phone("11999999999"), "(11) 99999-9999")

    def test_validate_signup_rejects_blank_values_after_trim(self):
        self.assertEqual(validate_signup("Ana", "ana@exemplo.com", "   "), "Preencha nome, email e senha para continuar.")

    def test_build_image_data_url_uses_base64_and_image_mime(self):
        data_url = build_image_data_url("avatar.png", b"\x89PNG\r\n\x1a\n")
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        self.assertIn("iVBORw0KGgo", data_url)

    def test_load_current_user_accepts_token_when_user_id_missing(self):
        state = AuthState.__new__(AuthState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "auth_token", "valid-token")
        object.__setattr__(state, "user_id", "")
        object.__setattr__(state, "user", {})
        object.__setattr__(state, "user_json", "")
        object.__setattr__(state, "user_role", "cliente")
        object.__setattr__(state, "user_full_name", "Ana")
        object.__setattr__(state, "user_email", "ana@exemplo.com")
        object.__setattr__(state, "session_validated", False)
        response = Mock(status_code=200)
        response.content = b'{"id": 29, "email": "ana@exemplo.com", "role": "cliente"}'
        response.json.return_value = {"id": 29, "email": "ana@exemplo.com", "role": "cliente"}

        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch("sosdrive.requests.get", return_value=response),
        ):
            state.load_current_user()

        self.assertEqual(state.user_id, "29")
        self.assertEqual(state.user_role, "cliente")

    def test_signup_sets_duplicate_email_message_from_backend_conflict(self):
        self.assertTrue(
            _is_duplicate_email_error(409, "Este e-mail já está cadastrado. Faça login ou tente outro.")
        )
        self.assertTrue(_is_duplicate_email_error(409, "Email already exists"))
        self.assertFalse(_is_duplicate_email_error(400, "Mensagem genérica do backend"))

    def test_fetch_user_profile_returns_empty_profile_for_missing_record(self):
        response = Mock(status_code=404)
        with patch("sosdrive.requests.get", return_value=response):
            self.assertEqual(fetch_user_profile("token", "https://xano.example/api"), {})

    def test_customer_request_stays_searching_until_provider_accepts(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "user_vehicles", [{"id": 1, "brand": "Toyota", "model": "Corolla", "plate": "ABC-1234"}])
        object.__setattr__(state, "selected_vehicle_id", 1)
        object.__setattr__(state, "client_location", {"lat": -23.55, "lng": -46.63})
        object.__setattr__(state, "selected_service", None)
        object.__setattr__(state, "request_status", "idle")
        object.__setattr__(state, "request_id", None)
        object.__setattr__(state, "request_server_status", "")
        object.__setattr__(state, "request_estimated_price", 0.0)
        object.__setattr__(state, "request_distance_km", 0.0)
        object.__setattr__(state, "request_error_message", "")
        object.__setattr__(state, "show_profile_link", False)
        object.__setattr__(state, "pending_service_type", "")

        original_queue = pending_provider_requests[:]
        pending_provider_requests.clear()
        try:
            object.__setattr__(state, "_get_auth_token", AsyncMock(return_value="token-123"))
            with patch("sosdrive.request_service_xano", return_value={"request_id": 99, "status": "queued", "estimated_price": 150.0, "distance_km": 4.4}):
                asyncio.run(state._submit_customer_request("tire"))

            self.assertEqual(state.request_status, "searching")
            self.assertEqual(state.request_id, 99)
            self.assertEqual(pending_provider_requests, [])
        finally:
            pending_provider_requests[:] = original_queue

    def test_save_user_profile_sends_only_profile_fields(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 4, "user_id": 9, "nome_completo": "Ana"}
        payload = {
            "nome_completo": " Ana ",
            "cpf": "123.456.789-01",
            "telefone": "(11) 99999-9999",
            "foto_perfil": None,
        }
        with patch("sosdrive.requests.request", return_value=response) as request:
            result = save_user_profile("token", "https://xano.example/api", payload, "POST")

        self.assertEqual(result["user_id"], 9)
        self.assertEqual(request.call_args.args[0], "POST")
        self.assertEqual(request.call_args.args[1], "https://xano.example/api/user_profile")
        self.assertEqual(
            request.call_args.kwargs["headers"]["Content-Type"],
            "application/json",
        )
        self.assertEqual(
            request.call_args.kwargs["headers"]["Authorization"],
            "Bearer token",
        )
        request.assert_called_once_with(
            "POST",
            "https://xano.example/api/user_profile",
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
            json={
                "nome_completo": "Ana",
                "cpf": "12345678901",
                "telefone": "11999999999",
                "foto_perfil": "",
            },
            timeout=10,
        )

    def test_save_user_profile_uses_empty_strings_and_omits_non_text_fields(self):
        response = Mock(status_code=200)
        response.json.return_value = {"nome_completo": ""}
        payload = {
            "nome_completo": None,
            "cpf": None,
            "telefone": "",
            "foto_perfil": {"unexpected": "value"},
        }
        with patch("sosdrive.requests.request", return_value=response) as request:
            save_user_profile("token", "https://xano.example/api", payload, "PUT")

        self.assertEqual(request.call_args.args[0], "PUT")
        self.assertEqual(request.call_args.args[1], "https://xano.example/api/user_profile")
        self.assertEqual(
            request.call_args.kwargs["headers"]["Content-Type"],
            "application/json",
        )
        self.assertEqual(
            request.call_args.kwargs["json"],
            {"nome_completo": "", "cpf": "", "telefone": "", "foto_perfil": ""},
        )

    def test_save_user_profile_sends_photo_url_as_json_string(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 4, "user_id": 9, "nome_completo": "Ana", "foto_perfil": "https://cdn.example/avatar.png"}
        payload = {
            "nome_completo": " Ana ",
            "cpf": "123.456.789-01",
            "telefone": "(11) 99999-9999",
            "foto_perfil": "https://xano.example/vault/profile/avatar.png",
        }

        with patch("sosdrive.requests.request", return_value=response) as request:
            result = save_user_profile(
                "token",
                "https://xano.example/api",
                payload,
                "POST",
            )

        self.assertEqual(result["foto_perfil"], "https://cdn.example/avatar.png")
        request.assert_called_once()
        call_kwargs = request.call_args.kwargs
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer token")
        self.assertIn("json", call_kwargs)
        self.assertNotIn("files", call_kwargs)
        self.assertEqual(
            call_kwargs["json"],
            {
                "nome_completo": "Ana",
                "cpf": "12345678901",
                "telefone": "11999999999",
                "foto_perfil": "https://xano.example/vault/profile/avatar.png",
            },
        )

    def test_upload_user_profile_photo_sends_multipart_and_returns_public_url(self):
        response = Mock(status_code=200)
        response.json.return_value = {"path": "/vault/profile/avatar.png"}
        profile_file = {
            "field_name": "foto_perfil",
            "name": "avatar.png",
            "content": b"png-content",
            "mime_type": "image/png",
        }

        with patch("sosdrive.requests.post", return_value=response) as request:
            url = upload_user_profile_photo(
                "token",
                "https://xano.example/api:profile",
                profile_file,
            )

        self.assertEqual(url, "https://xano.example/vault/profile/avatar.png")
        self.assertEqual(request.call_count, 1)
        args, kwargs = request.call_args
        self.assertEqual(
            args,
            ("https://xano.example/api:profile/user_profile/photo",),
        )
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer token"})
        self.assertEqual(
            kwargs["files"],
            {"foto_perfil": ("avatar.png", b"png-content", "image/png")},
        )
        self.assertEqual(kwargs["timeout"], 10)


if __name__ == "__main__":
    unittest.main()
