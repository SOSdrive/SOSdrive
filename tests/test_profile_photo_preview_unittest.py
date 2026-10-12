import base64
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import reflex as rx
import requests

from sosdrive import AuthState, build_image_data_url


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
)
JPEG_BYTES = b"\xff\xd8\xffprofile-image-content"


def make_profile_state(**overrides):
    state = AuthState.__new__(AuthState)
    object.__setattr__(state, "dirty_vars", set())
    values = {
        "auth_token": "auth-token",
        "user_id": "42",
        "user_role": "cliente",
        "user_full_name": "Beatriz Alves",
        "user_profile_photo": "https://cdn.example/saved.png",
        "selected_profile_image": "",
        "selected_profile_filename": "",
        "selected_profile_uploaded_url": "",
        "user_cpf": "",
        "user_phone": "",
        "profile_exists": True,
        "profile_error": "",
        "profile_message": "",
        "profile_is_loading": False,
    }
    values.update(overrides)
    for name, value in values.items():
        object.__setattr__(state, name, value)
    return state


class TestProfilePhotoPreview(unittest.TestCase):
    def test_upload_handler_stages_png_without_replacing_persisted_photo(self):
        state = make_profile_state()
        uploaded_file = rx.UploadFile(
            file=io.BytesIO(PNG_BYTES),
            path=Path("avatar.png"),
            size=len(PNG_BYTES),
        )

        state.handle_profile_upload([uploaded_file])

        self.assertTrue(state.selected_profile_image.startswith("data:image/png;base64,"))
        self.assertEqual(state.selected_profile_filename, "avatar.png")
        self.assertEqual(state.user_profile_photo, "https://cdn.example/saved.png")
        self.assertEqual(state.profile_photo_preview, state.selected_profile_image)
        self.assertEqual(state.profile_error, "")

    def test_upload_handler_uses_content_mime_and_rejects_invalid_file(self):
        state = make_profile_state(
            selected_profile_image="data:image/png;base64,previous",
            selected_profile_filename="previous.png",
            selected_profile_uploaded_url="https://cdn.example/old.png",
        )
        uploaded_file = rx.UploadFile(
            file=io.BytesIO(JPEG_BYTES),
            path=Path("avatar.jpeg"),
            size=len(JPEG_BYTES),
        )

        state.handle_profile_upload([uploaded_file])
        self.assertTrue(state.selected_profile_image.startswith("data:image/jpeg;base64,"))
        self.assertEqual(state.selected_profile_filename, "avatar.jpeg")
        self.assertEqual(state.selected_profile_uploaded_url, "")

        invalid_file = rx.UploadFile(
            file=io.BytesIO(b"not an image"),
            path=Path("avatar.png"),
            size=12,
        )
        previous_preview = state.selected_profile_image
        previous_filename = state.selected_profile_filename
        state.handle_profile_upload([invalid_file])

        self.assertEqual(state.selected_profile_image, previous_preview)
        self.assertEqual(state.selected_profile_filename, previous_filename)
        self.assertEqual(state.profile_error, "Não foi possível carregar a imagem selecionada.")

    def test_upload_handler_rejects_empty_and_missing_files(self):
        state = make_profile_state()
        state.handle_profile_upload([])
        self.assertEqual(state.selected_profile_image, "")

        state.handle_profile_upload([
            rx.UploadFile(file=io.BytesIO(b""), path=Path("empty.png"), size=0)
        ])
        self.assertEqual(state.selected_profile_image, "")
        self.assertTrue(state.profile_error)

    def test_avatar_source_falls_back_to_persisted_photo_then_initials(self):
        state = make_profile_state(
            user_profile_photo="https://cdn.example/saved.png",
            selected_profile_image="",
        )
        self.assertEqual(state.profile_photo_preview, "https://cdn.example/saved.png")
        self.assertEqual(state.user_initials, "BA")

        state.user_profile_photo = ""
        self.assertEqual(state.profile_photo_preview, "")
        self.assertEqual(state.user_initials, "BA")

    def test_build_image_data_url_rejects_mime_extension_mismatch(self):
        with self.assertRaises(ValueError):
            build_image_data_url("avatar.png", JPEG_BYTES)

    def test_failed_save_keeps_staged_photo_for_retry(self):
        staged_image = build_image_data_url("picked.jpg", JPEG_BYTES)
        state = make_profile_state(
            selected_profile_image=staged_image,
            selected_profile_filename="picked.jpg",
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.upload_user_profile_photo",
                return_value="https://xano.example/vault/picked.jpg",
            ),
            patch("sosdrive.save_user_profile", side_effect=requests.ConnectionError),
        ):
            state.save_profile()

        self.assertEqual(state.selected_profile_image, staged_image)
        self.assertEqual(state.selected_profile_filename, "picked.jpg")
        self.assertEqual(state.selected_profile_uploaded_url, "https://xano.example/vault/picked.jpg")
        self.assertEqual(state.profile_photo_preview, staged_image)
        self.assertFalse(state.profile_is_loading)
        self.assertEqual(state.profile_message, "")
        self.assertTrue(state.profile_error)

    def test_upload_failure_does_not_send_profile_and_keeps_draft(self):
        staged_image = build_image_data_url("picked.jpg", JPEG_BYTES)
        state = make_profile_state(
            selected_profile_image=staged_image,
            selected_profile_filename="picked.jpg",
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.upload_user_profile_photo",
                side_effect=requests.ConnectionError,
            ),
            patch("sosdrive.save_user_profile") as save_profile,
        ):
            state.save_profile()

        save_profile.assert_not_called()
        self.assertEqual(state.selected_profile_image, staged_image)
        self.assertEqual(state.selected_profile_uploaded_url, "")
        self.assertEqual(state.profile_message, "")
        self.assertTrue(state.profile_error)
        self.assertFalse(state.profile_is_loading)

    def test_retry_reuses_photo_url_when_profile_save_failed(self):
        staged_image = build_image_data_url("picked.jpg", JPEG_BYTES)
        photo_url = "https://xano.example/vault/picked.jpg"
        state = make_profile_state(
            selected_profile_image=staged_image,
            selected_profile_filename="picked.jpg",
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.upload_user_profile_photo",
                return_value=photo_url,
            ) as upload_photo,
            patch(
                "sosdrive.save_user_profile",
                side_effect=[
                    requests.ConnectionError,
                    {"foto_perfil": photo_url},
                ],
            ) as save_profile,
        ):
            state.save_profile()
            state.save_profile()

        upload_photo.assert_called_once()
        self.assertEqual(save_profile.call_count, 2)
        self.assertEqual(save_profile.call_args.args[2]["foto_perfil"], photo_url)
        self.assertEqual(state.user_profile_photo, photo_url)
        self.assertEqual(state.selected_profile_image, "")
        self.assertEqual(state.selected_profile_uploaded_url, "")
        self.assertEqual(state.profile_message, "Dados atualizados com sucesso.")

    def test_save_profile_sends_normalized_primitive_text_fields(self):
        state = make_profile_state(
            user_full_name="  Beatriz Alves  ",
            user_cpf="123.456.789-01",
            user_phone="(11) 99999-9999",
            selected_profile_image="",
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.save_user_profile",
                return_value={"nome_completo": "Beatriz Alves"},
            ) as save_profile,
            patch("sosdrive.upload_user_profile_photo") as upload_photo,
        ):
            state.save_profile()

        payload = save_profile.call_args.args[2]
        self.assertEqual(
            payload,
            {
                "nome_completo": "Beatriz Alves",
                "cpf": "12345678901",
                "telefone": "11999999999",
                "foto_perfil": "https://cdn.example/saved.png",
            },
        )
        self.assertTrue(all(isinstance(value, str) for value in payload.values()))
        self.assertEqual(save_profile.call_args.args[3], "PUT")
        upload_photo.assert_not_called()
        self.assertEqual(state.profile_message, "Dados atualizados com sucesso.")
        self.assertFalse(state.profile_is_loading)

    def test_save_profile_creates_profile_without_requiring_user_id_in_url(self):
        state = make_profile_state(profile_exists=False, user_id="")
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch("sosdrive.save_user_profile", return_value={}) as save_profile,
        ):
            state.save_profile()

        self.assertEqual(save_profile.call_args.args[1], "https://xano.example/api")
        self.assertEqual(save_profile.call_args.args[3], "POST")
        self.assertEqual(save_profile.call_args.args[0], state.auth_token)

    def test_save_profile_converts_missing_optional_fields_to_empty_strings(self):
        state = make_profile_state(user_cpf=None, user_phone=None)
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch("sosdrive.save_user_profile", return_value={}) as save_profile,
        ):
            state.save_profile()

        self.assertEqual(
            save_profile.call_args.args[2],
            {
                "nome_completo": "Beatriz Alves",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "https://cdn.example/saved.png",
            },
        )

    def test_successful_save_uploads_image_metadata_and_clears_draft(self):
        staged_image = build_image_data_url("picked.jpg", JPEG_BYTES)
        state = make_profile_state(
            selected_profile_image=staged_image,
            selected_profile_filename="picked.jpg",
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api"}),
            patch(
                "sosdrive.save_user_profile",
                return_value={"foto_perfil": "https://cdn.example/picked.jpg"},
            ) as save_profile,
            patch(
                "sosdrive.upload_user_profile_photo",
                return_value="https://cdn.example/picked.jpg",
            ) as upload_photo,
        ):
            state.save_profile()

        uploaded_file = upload_photo.call_args.args[2]
        self.assertEqual(
            save_profile.call_args.args[2],
            {
                "nome_completo": "Beatriz Alves",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "https://cdn.example/picked.jpg",
            },
        )
        self.assertEqual(uploaded_file["name"], "picked.jpg")
        self.assertEqual(uploaded_file["mime_type"], "image/jpeg")
        self.assertEqual(uploaded_file["content"], JPEG_BYTES)
        self.assertEqual(state.user_profile_photo, "https://cdn.example/picked.jpg")
        self.assertEqual(state.selected_profile_image, "")
        self.assertEqual(state.selected_profile_filename, "")
        self.assertEqual(state.selected_profile_uploaded_url, "")
        self.assertEqual(state.profile_photo_preview, "https://cdn.example/picked.jpg")


if __name__ == "__main__":
    unittest.main()
