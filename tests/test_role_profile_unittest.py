import unittest
from unittest.mock import Mock, patch

from sosdrive import (
    UnsupportedRoleError,
    _is_duplicate_email_error,
    build_image_data_url,
    fetch_user_profile,
    format_cpf,
    format_phone,
    normalize_user_role,
    save_user_profile,
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

    def test_save_user_profile_sends_only_profile_fields(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 4, "user_id": 9, "nome_completo": "Ana"}
        payload = {
            "nome_completo": "Ana",
            "cpf": "12345678901",
            "telefone": "11999999999",
            "foto_perfil": None,
        }
        with patch("sosdrive.requests.request", return_value=response) as request:
            result = save_user_profile("token", "https://xano.example/api", payload, "POST")

        self.assertEqual(result["user_id"], 9)
        request.assert_called_once_with(
            "POST",
            "https://xano.example/api/user_profile",
            headers={"Authorization": "Bearer token"},
            json=payload,
            timeout=10,
        )

    def test_save_user_profile_uses_multipart_for_image_upload(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": 4, "user_id": 9, "nome_completo": "Ana", "foto_perfil": "https://cdn.example/avatar.png"}
        payload = {"nome_completo": "Ana", "cpf": "12345678901", "telefone": "11999999999"}
        profile_file = {"field_name": "foto_perfil", "name": "avatar.png", "content": b"fakeimage", "mime_type": "image/png"}

        with patch("sosdrive.requests.request", return_value=response) as request:
            result = save_user_profile(
                "token",
                "https://xano.example/api",
                payload,
                "POST",
                profile_file=profile_file,
            )

        self.assertEqual(result["foto_perfil"], "https://cdn.example/avatar.png")
        request.assert_called_once()
        call_kwargs = request.call_args.kwargs
        self.assertEqual(call_kwargs["headers"], {"Authorization": "Bearer token"})
        self.assertIn("files", call_kwargs)
        self.assertIn("data", call_kwargs)
        self.assertEqual(call_kwargs["files"]["foto_perfil"][0], "avatar.png")


if __name__ == "__main__":
    unittest.main()
