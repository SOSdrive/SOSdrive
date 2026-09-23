import unittest
from unittest.mock import Mock, patch

from sosdrive import (
    UnsupportedRoleError,
    fetch_user_profile,
    format_cpf,
    format_phone,
    normalize_user_role,
    save_user_profile,
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


if __name__ == "__main__":
    unittest.main()
