from __future__ import annotations

"""SOS Drive Reflex application."""


import reflex as rx
import requests
import os
import math
import time
import asyncio
import json
import logging
import base64
import binascii
from pathlib import Path
from urllib.parse import urlsplit
from collections.abc import Callable

from dotenv import load_dotenv

from styles import GLOBAL_STYLE, COLORS


def _load_project_environment(env_file: Path | None = None) -> bool:
    """Load project-local environment settings without overriding process values."""
    return load_dotenv(
        dotenv_path=env_file or Path(__file__).with_name(".env"),
        override=False,
    )


_load_project_environment()

logger = logging.getLogger(__name__)
pending_provider_requests: list[dict] = [] # Deprecated: Use Xano polling
LOGIN_BACKGROUND_VIDEO_URL = "/Pippit_0924_TruckTracking.mp4"


def validate_signup(name: str, email: str, password: str) -> str:
    """Return a local signup validation message, or an empty string."""
    if not all((name.strip(), email.strip(), password.strip())):
        return "Preencha nome, email e senha para continuar."
    return ""


def digits_only(value: str) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def build_image_data_url(file_name: str, content: bytes) -> str:
    """Convert a selected profile image into a base64 data URL supported by the frontend."""
    extension = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
        if extension and extension != "png":
            raise ValueError("Selecione uma imagem PNG ou JPEG válida.")
    elif content.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
        if extension and extension not in {"jpg", "jpeg"}:
            raise ValueError("Selecione uma imagem PNG ou JPEG válida.")
    else:
        raise ValueError("Selecione uma imagem PNG ou JPEG válida.")
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def format_cpf(value: str) -> str:
    digits = digits_only(value)[:11]
    if len(digits) <= 3:
        return digits
    if len(digits) <= 6:
        return f"{digits[:3]}.{digits[3:]}"
    if len(digits) <= 9:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_phone(value: str) -> str:
    digits = digits_only(value)[:11]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 7:
        return f"({digits[:2]}) {digits[2:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"


class InvalidCredentialsError(Exception):
    """Raised when Xano rejects authentication credentials."""

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class SignupConflictError(Exception):
    """Raised when Xano rejects a signup because the email already exists."""


class XanoAPIError(Exception):
    """Raised when Xano returns a structured API error."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class XanoConfigurationError(RuntimeError):
    """Raised when the Xano API base URL is missing or invalid."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class XanoMalformedResponseError(XanoAPIError):
    """Raised when Xano returns a success response that violates its contract."""


class UnsupportedRoleError(Exception):
    """Raised when an authenticated user has an unsupported role."""


def normalize_user_role(role: str | None) -> str:
    """Normalize legacy role values and reject unknown account types."""
    normalized_role = (role or "").strip().lower()
    role_aliases = {"client": "cliente", "provider": "prestador"}
    normalized_role = role_aliases.get(normalized_role, normalized_role)
    if normalized_role not in {"cliente", "prestador"}:
        raise UnsupportedRoleError()
    return normalized_role


def _response_message(response: requests.Response) -> str:
    """Extract the useful Xano error message without exposing secrets."""
    try:
        body = response.json()
    except ValueError:
        return response.text.strip() or f"HTTP {response.status_code}"
    if isinstance(body, dict):
        return str(body.get("message") or body.get("error") or body.get("code") or body)
    return str(body)


def _safe_login_error_message(response_body: object) -> str:
    """Return a short, user-facing Xano login error without exposing response data."""
    if not isinstance(response_body, dict):
        return ""
    for key in ("message", "error"):
        message = response_body.get(key)
        if isinstance(message, str):
            message = message.strip()
            if message and len(message) <= 240:
                return message
    return ""


def _validate_xano_api_url(api_url: str) -> str:
    """Return a normalized HTTP(S) Xano API base URL."""
    normalized_url = api_url.strip().rstrip("/")
    try:
        parsed_url = urlsplit(normalized_url)
        valid_url = (
            parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.hostname)
            and parsed_url.username is None
            and parsed_url.password is None
            and parsed_url.port != 0
            and not parsed_url.query
            and not parsed_url.fragment
        )
    except ValueError:
        valid_url = False
    if not valid_url:
        raise XanoConfigurationError("invalid")
    return normalized_url


def _safe_xano_endpoint(endpoint: str) -> str:
    """Return endpoint context without credentials, query strings, or fragments."""
    try:
        parsed_url = urlsplit(endpoint)
        hostname = parsed_url.hostname
        if not hostname or parsed_url.scheme not in {"http", "https"}:
            return "<invalid Xano endpoint>"
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        port = parsed_url.port
        host = f"{hostname}:{port}" if port is not None else hostname
        return f"{parsed_url.scheme}://{host}{parsed_url.path}"
    except ValueError:
        return "<invalid Xano endpoint>"


def _is_duplicate_email_error(status_code: int, message: str) -> bool:
    normalized_message = message.lower()
    duplicate_markers = (
        "already exists",
        "already in use",
        "already registered",
        "duplicate",
        "unique",
        "email exists",
        "e-mail já está em uso",
    )
    return status_code == 409 or any(marker in normalized_message for marker in duplicate_markers)


def _auth_headers(auth_token: str) -> dict[str, str]:
    """Build the only authenticated Xano request header used by the client."""
    if not auth_token:
        raise ValueError("Authentication token is required")
    return {"Authorization": "Bearer " + auth_token}


def authenticate_with_xano(path: str, payload: dict, api_url: str) -> tuple[str, int]:
    """Call an Xano auth endpoint and return its token and user ID."""
    normalized_url = _validate_xano_api_url(api_url)
    endpoint = f"{normalized_url}{path}"
    safe_endpoint = _safe_xano_endpoint(endpoint)
    logger.info("Xano request: POST %s", safe_endpoint)
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    try:
        response_body = response.json()
    except ValueError:
        response_body = None
    logger.info("Xano response: POST %s status=%s", safe_endpoint, response.status_code)

    if response.status_code >= 400:
        message = (
            _safe_login_error_message(response_body)
            if path == "/auth/login"
            else _response_message(response)
        )
        if path == "/auth/signup" and _is_duplicate_email_error(response.status_code, message):
            raise SignupConflictError()
        if path == "/auth/login" and response.status_code in {400, 401, 403}:
            raise InvalidCredentialsError(message)
        raise XanoAPIError(response.status_code, message if path != "/auth/login" else "")

    response_payload = response_body
    if not isinstance(response_payload, dict):
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned an invalid authentication response",
        )
    auth_token = response_payload.get("authToken") or response_payload.get("token")
    user = response_payload.get("user")
    response_user_id = response_payload.get("user_id") or response_payload.get("id")
    if response_user_id is None and isinstance(user, dict):
        response_user_id = user.get("user_id") or user.get("id")
    try:
        user_id = int(response_user_id)
    except (TypeError, ValueError):
        user_id = 0
    if not isinstance(auth_token, str) or not auth_token.strip() or user_id <= 0:
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned an invalid authentication response",
        )
    return auth_token.strip(), user_id


def login_with_xano(email: str, password: str, api_url: str) -> tuple[str, int]:
    """Authenticate a driver through Xano."""
    return authenticate_with_xano(
        "/auth/login",
        {"email": email.strip().lower(), "password": password},
        api_url,
    )


def fetch_authenticated_user(auth_token: str, api_url: str, user_id: str = "") -> dict:
    """Fetch and validate the user associated with an authentication token."""
    current_user_id = int(user_id) if user_id and str(user_id).strip() else None
    endpoint = f"{_validate_xano_api_url(api_url)}/auth/me"
    safe_endpoint = _safe_xano_endpoint(endpoint)
    logger.info("Xano request: GET %s user_id=%s", safe_endpoint, current_user_id)
    response = requests.get(
        endpoint,
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    logger.info("Xano response: GET %s status=%s", safe_endpoint, response.status_code)
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, "Xano user lookup failed")
    try:
        user = response.json()
    except ValueError as error:
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned an invalid user response",
        ) from error
    if not isinstance(user, dict):
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned an invalid user response",
        )
    response_user_id = user.get("id") or user.get("user_id")
    try:
        response_user_id = int(response_user_id) if response_user_id is not None else None
    except (TypeError, ValueError) as error:
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned an invalid user identity",
        ) from error
    if current_user_id is not None and response_user_id is not None and response_user_id != current_user_id:
        raise XanoMalformedResponseError(
            response.status_code,
            "Xano returned a mismatched user identity",
        )
    return user


def signup_with_xano(
    name: str,
    email: str,
    password: str,
    role: str,
    api_url: str,
) -> tuple[str, int]:
    """Create an account through Xano."""
    return authenticate_with_xano(
        "/auth/signup",
        {
            "name": name.strip(),
            "email": email.strip().lower(),
            "password": password,
            "role": role,
        },
        api_url,
    )


def fetch_user_profile(auth_token: str, api_url: str) -> dict:
    """Fetch the profile associated with the current Xano token."""
    response = requests.get(
        f"{api_url.rstrip('/')}/user_profile",
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    payload = response.json()
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Unexpected profile response")
    return payload


def save_user_profile(
    auth_token: str,
    api_url: str,
    payload: dict,
    method: str,
) -> dict:
    """Create or update the profile owned by the current Xano token."""
    headers = {
        **_auth_headers(auth_token),
        "Content-Type": "application/json",
    }
    request_kwargs = {"headers": headers, "timeout": 10}
    text_payload = {
        "nome_completo": str(payload.get("nome_completo") or "").strip(),
        "cpf": digits_only(payload.get("cpf")),
        "telefone": digits_only(payload.get("telefone")),
        "foto_perfil": (
            payload["foto_perfil"].strip()
            if isinstance(payload.get("foto_perfil"), str)
            else ""
        ),
    }

    request_kwargs["json"] = text_payload

    response = requests.request(
        method,
        f"{api_url.rstrip('/')}/user_profile",
        **request_kwargs,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, _response_message(response))
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Unexpected profile response")
    return result


def upload_user_profile_photo(
    auth_token: str,
    api_url: str,
    profile_file: dict,
) -> str:
    """Upload a profile image and return its stable public URL."""
    parsed_api_url = urlsplit(_validate_xano_api_url(api_url))
    response = requests.post(
        f"{api_url.rstrip('/')}/user_profile/photo",
        headers=_auth_headers(auth_token),
        files={
            profile_file.get("field_name", "foto_perfil"): (
                profile_file.get("name", "profile-image"),
                profile_file.get("content", b""),
                profile_file.get("mime_type", "image/png"),
            )
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, _response_message(response))
    result = response.json()
    if not isinstance(result, dict):
        raise XanoAPIError(response.status_code, "Xano returned an invalid upload response")
    path = result.get("path")
    if not isinstance(path, str) or not path.startswith("/vault/"):
        raise XanoAPIError(response.status_code, "Xano returned an invalid upload path")
    return f"{parsed_api_url.scheme}://{parsed_api_url.netloc}{path}"


def get_xano_services_url() -> str:
    """Return the base URL for service and vehicle endpoints."""
    configured_url = os.getenv("XANO_SERVICES_URL", "").strip().rstrip("/")
    if configured_url:
        return configured_url

    api_url = os.getenv("XANO_API_URL", "").strip().rstrip("/")
    if api_url:
        # Ensure we use the same API group as the main auth API to avoid 404s
        # If api_url is '.../api:9gPvpDtO', we stay in that group.
        return api_url

    return ""


def fetch_user_vehicles_xano(auth_token: str, api_url: str) -> list[dict]:
    """Fetch the authenticated user's vehicles from Xano."""
    endpoint = f"{api_url.rstrip('/')}/my_vehicles"
    response = requests.get(
        endpoint,
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, _response_message(response))
    result = response.json()
    return result if isinstance(result, list) else []


def fetch_pending_requests_xano(auth_token: str, api_url: str) -> list[dict]:
    """Fetch all pending service requests from Xano for providers."""
    endpoint = f"{api_url.rstrip('/')}/pending_requests"
    response = requests.get(
        endpoint,
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, _response_message(response))
    result = response.json()
    return result if isinstance(result, list) else []


def request_service_xano(
    auth_token: str,
    api_url: str,
    service_type: str,
    vehicle_id: int,
    latitude: float,
    longitude: float,
) -> dict:
    """Create a service request through Xano."""
    response = requests.post(
        f"{api_url.rstrip('/')}/request_service",
        json={
            "service_type": service_type,
            "vehicle_id": vehicle_id,
            "latitude": latitude,
            "longitude": longitude,
        },
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, _response_message(response))
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Unexpected service request response")
    return result


def release_service_request_xano(
    auth_token: str,
    api_url: str,
    request_id: int,
) -> dict:
    """Release an assigned request back to the pending queue."""
    rid = int(request_id)
    endpoint = f"{api_url.rstrip('/')}/update_request_status"

    logger.info("Xano release request: POST %s", _safe_xano_endpoint(endpoint))

    response = requests.post(
        endpoint,
        json={"request_id": rid, "status": "pending"},
        headers=_auth_headers(auth_token),
        timeout=10,
    )

    if response.status_code >= 400:
        logger.error("Xano Update Failed: status=%s", response.status_code)
        raise XanoAPIError(response.status_code, _response_message(response))

    return response.json()


def accept_service_request_xano(
    auth_token: str,
    api_url: str,
    request_id: int,
) -> dict:
    """Assign a pending service request to the authenticated provider in Xano."""
    rid = int(request_id)
    endpoint = f"{api_url.rstrip('/')}/{rid}/accept"
    safe_endpoint = _safe_xano_endpoint(endpoint)
    response = requests.post(
        endpoint,
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        logger.error(
            "Xano service request acceptance failed endpoint=%s status=%s",
            safe_endpoint,
            response.status_code,
        )
        raise XanoAPIError(response.status_code, "Service request acceptance failed")
    try:
        result = response.json()
    except ValueError as error:
        raise ValueError("Unexpected service request acceptance response") from error
    if not isinstance(result, dict):
        raise ValueError("Unexpected service request acceptance response")
    return result


def complete_service_request_xano(
    auth_token: str,
    api_url: str,
    request_id: int,
) -> dict:
    """Complete an accepted or in-progress service request through Xano."""
    rid = int(request_id)
    endpoint = f"{api_url.rstrip('/')}/{rid}/status"
    response = requests.patch(
        endpoint,
        json={"status": "completed"},
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        logger.error("Xano completion failed: status=%s", response.status_code)
        raise XanoAPIError(response.status_code, _response_message(response))
    return response.json()


def send_service_message_xano(
    auth_token: str,
    api_url: str,
    request_id: int,
    message_text: str,
) -> dict:
    """Send a message from provider to client in Xano."""
    rid = int(request_id)
    endpoint = f"{api_url.rstrip('/')}/{rid}/messages"
    safe_endpoint = _safe_xano_endpoint(endpoint)

    response = requests.post(
        endpoint,
        json={"message_text": message_text},
        headers=_auth_headers(auth_token),
        timeout=10,
    )

    if response.status_code >= 400:
        logger.error(
            "Xano service message failed endpoint=%s status=%s",
            safe_endpoint,
            response.status_code,
        )
        raise XanoAPIError(response.status_code, "Service message request failed")

    try:
        result = response.json()
    except ValueError as error:
        raise ValueError("Unexpected service message response") from error
    if not isinstance(result, dict):
        raise ValueError("Unexpected service message response")
    logger.info("Xano service message sent endpoint=%s", safe_endpoint)
    return result


def fetch_service_messages_xano(
    auth_token: str,
    api_url: str,
    request_id: int,
) -> list[dict]:
    """Fetch the conversation for a service request from Xano."""
    rid = int(request_id)
    endpoint = f"{api_url.rstrip('/')}/{rid}/messages"
    safe_endpoint = _safe_xano_endpoint(endpoint)
    response = requests.get(
        endpoint,
        headers=_auth_headers(auth_token),
        timeout=10,
    )
    if response.status_code >= 400:
        raise XanoAPIError(response.status_code, "Service messages request failed")
    try:
        result = response.json()
    except ValueError as error:
        raise ValueError("Unexpected service messages response") from error
    if not isinstance(result, list):
        raise ValueError("Unexpected service messages response")
    logger.info("Xano service messages loaded endpoint=%s count=%s", safe_endpoint, len(result))
    return result


def build_atendimento_mock(request: dict, provider_coords: list[float]) -> dict:
    """Build a local/mock attendance payload from one accepted request."""
    return {
        "id": request.get("id", 0),
        "nome": request.get("user", "Usuário"),
        "tipo_problema": request.get("type", "Solicitação"),
        "veiculo": request.get("vehicle", "Veículo não informado"),
        "endereco": request.get("address", "Endereço não informado"),
        "observacao": request.get("note", "Sem observações."),
        "phone": request.get("phone", ""),
        "distance": request.get("distance", "0.0 km"),
        "eta": request.get("eta", "15 min"),
        "maps_url": request.get("maps_url", "#"),
        "user_coords": request.get("coords", [-23.5505, -46.6333]),
        "provider_coords": provider_coords,
        "service_icon": request.get("service_icon", "🛠️"),
    }


class AuthState(rx.State):
    """Application state for navigation and driver authentication."""

    screen: str = "presentation"
    user_role: str = "cliente"
    email: str = ""
    password: str = ""
    signup_name: str = ""
    signup_email: str = ""
    signup_password: str = ""
    signup_role: str = "cliente"
    auth_token: str = ""
    user_json: str = ""
    user: dict = {}
    user_id: str = ""
    error_message: str = ""
    signup_message: str = ""
    is_loading: bool = False
    active_call_status: str | None = None
    active_call_eta: str = "15 min"

    # Profile Fields (Mock)
    user_profile_photo: str = ""
    selected_profile_image: str = ""
    selected_profile_filename: str = ""
    selected_profile_uploaded_url: str = ""
    user_full_name: str = "Usuário SOS"
    user_email: str = "usuario@exemplo.com"
    user_phone: str = "(11) 99999-9999"
    user_cpf: str = ""
    profile_exists: bool = False
    profile_error: str = ""
    profile_message: str = ""
    profile_is_loading: bool = False
    session_validated: bool = False

    @rx.var
    def is_authenticated(self) -> bool:
        return bool(self.auth_token)

    @rx.var
    def user_initials(self) -> str:
        """Compute initials from user_full_name."""
        names = self.user_full_name.split()
        if not names:
            return "U"
        first = names[0][0].upper()
        last = names[-1][0].upper() if len(names) > 1 else ""
        return f"{first}{last}"

    @rx.var
    def profile_photo_preview(self) -> str:
        """Return the staged profile image before the persisted photo."""
        return self.selected_profile_image or self.user_profile_photo

    def open_signup(self) -> None:
        return rx.redirect("/signup")

    def open_login(self) -> None:
        return rx.redirect("/login")

    def choose_signup_role(self, role: str) -> None:
        if role in {"cliente", "prestador"}:
            self.signup_role = role

    def set_signup_name(self, value: str) -> None:
        self.signup_name = value

    def set_signup_email(self, value: str) -> None:
        self.signup_email = value

    def set_signup_password(self, value: str) -> None:
        self.signup_password = value

    def signup(self) -> None:
        self.signup_message = ""
        self.error_message = ""

        clean_name = (self.signup_name or "").strip()
        clean_email = (self.signup_email or "").strip()
        clean_password = self.signup_password or ""
        self.signup_name = clean_name
        self.signup_email = clean_email

        self.error_message = validate_signup(
            clean_name,
            clean_email,
            clean_password,
        )
        if self.error_message:
            self.signup_password = ""
            return
        self.is_loading = True
        api_url = self.get_xano_api_url()
        if not api_url:
            self.error_message = "Não foi possível criar sua conta. Tente novamente."
            self.signup_password = ""
            self.is_loading = False
            return

        try:
            auth_token, user_id = signup_with_xano(
                clean_name,
                clean_email,
                clean_password,
                self.signup_role,
                api_url,
            )
            self.auth_token = auth_token
            self.user_id = str(user_id)
            self.load_current_user()
            self.signup_name = ""
            self.signup_email = ""
            self.signup_password = ""
            return self.redirect_to_user_home()
        except SignupConflictError:
            self.error_message = "Este e-mail já está cadastrado. Faça login ou tente outro."
        except XanoAPIError as error:
            self.error_message = error.message or "Não foi possível criar sua conta. Tente novamente."
        except (requests.RequestException, RuntimeError, ValueError) as error:
            logger.exception("Xano signup request failed: %s", error)
            self.error_message = "Não foi possível conectar ao Xano. Tente novamente."
        finally:
            self.signup_password = ""
            self.is_loading = False

    def set_email_value(self, value: str) -> None:
        self.email = value

    def set_password_value(self, value: str) -> None:
        self.password = value

    def return_to_presentation(self) -> None:
        return rx.redirect("/")

    def open_map_test(self) -> None:
        return rx.redirect("/test-map")

    def logout(self) -> None:
        self.clear_session()
        self.email = ""
        self.password = ""
        self.signup_name = ""
        self.signup_email = ""
        self.signup_password = ""
        self.error_message = ""
        self.signup_message = ""
        return rx.redirect("/login")

    def get_xano_api_url(self) -> str:
        configured_url = os.getenv("XANO_API_URL", "")
        if not configured_url.strip():
            return ""
        return configured_url.strip().rstrip("/")

    def set_authenticated_user(self, auth_token: str, user: dict) -> None:
        self.auth_token = auth_token
        self.session_validated = True
        self.user = user
        self.user_json = json.dumps(user)
        self.user_id = str(user.get("id", ""))
        self.user_role = normalize_user_role(user.get("role"))
        self.user_full_name = user.get("name", self.user_full_name)
        self.user_email = user.get("email", self.user_email)

    def clear_session(self) -> None:
        self.auth_token = ""
        self.user_json = ""
        self.user = {}
        self.user_id = ""
        self.user_role = "cliente"
        self.user_profile_photo = ""
        self.selected_profile_image = ""
        self.selected_profile_filename = ""
        self.selected_profile_uploaded_url = ""
        self.user_full_name = "Usuário SOS"
        self.user_email = "usuario@exemplo.com"
        self.user_phone = "(11) 99999-9999"
        self.user_cpf = ""
        self.profile_exists = False

    def expire_session(self):
        """Clear all authenticated state and return to login."""
        self.session_validated = False
        self.error_message = "Sua sessão expirou. Entre novamente."
        self.clear_session()
        return rx.redirect("/login")

    def load_current_user(self) -> None:
        """Load the authenticated user using the stored token and, when available, the cached user ID."""
        if not self.auth_token:
            raise RuntimeError("Authentication session is incomplete")

        user = fetch_authenticated_user(self.auth_token, self.get_xano_api_url(), self.user_id)
        response_user_id = user.get("id") or user.get("user_id")
        if response_user_id is not None:
            self.user_id = str(response_user_id)
        self.set_authenticated_user(self.auth_token, user)

    def redirect_to_user_home(self):
        if self.user_role == "prestador":
            return rx.redirect("/home_provider")
        return rx.redirect("/home_client")

    def redirect_to_user_profile(self):
        if self.user_role == "prestador":
            return rx.redirect("/perfil-prestador")
        if self.user_role == "cliente":
            return rx.redirect("/perfil-cliente")
        raise UnsupportedRoleError()

    def restore_session(self):
        """Restore the persisted user and validate the token with Xano."""
        self.session_validated = False
        if not self.auth_token:
            # Instead of immediately expiring, we can let them stay on the loading screen
            # or redirect to login. expire_session() is the correct way to handle this.
            return self.expire_session()

        try:
            if self.user_json:
                try:
                    self.user = json.loads(self.user_json)
                except json.JSONDecodeError:
                    self.user = {}
                self.user_id = str(self.user.get("id", self.user_id or ""))
                if self.user.get("role"):
                    self.user_role = normalize_user_role(self.user.get("role"))

            self.load_current_user()
            self.session_validated = True
        except (requests.RequestException, RuntimeError, ValueError, UnsupportedRoleError) as e:
            logger.error("Session restoration failed: %s", e)
            return self.expire_session()

    @rx.event
    async def login(self):
        """Authenticate through Xano without retaining the submitted password."""
        if self.is_loading:
            return
        self.error_message = ""
        self.is_loading = True
        connection_error = (
            "Erro ao conectar com o servidor Xano. "
            "Verifique a URL do endpoint ou sua conexão com a internet."
        )
        phase = "configuration"
        endpoint = ""

        yield
        redirect_event = None
        try:
            api_url = self.get_xano_api_url()
            if not api_url:
                raise XanoConfigurationError("missing")
            phase = "login"
            endpoint = f"{api_url}/auth/login"
            auth_token, user_id = await asyncio.to_thread(
                login_with_xano,
                self.email,
                self.password,
                api_url,
            )
            phase = "user_lookup"
            endpoint = f"{api_url}/auth/me"
            user = await asyncio.to_thread(
                fetch_authenticated_user,
                auth_token,
                api_url,
                str(user_id),
            )
            self.auth_token = auth_token
            self.user_id = str(user_id)
            self.set_authenticated_user(auth_token, user)
            redirect_event = self.redirect_to_user_profile()
        except UnsupportedRoleError:
            self.clear_session()
            self.error_message = "Sua conta não possui um tipo de usuário válido."
        except InvalidCredentialsError as error:
            self.clear_session()
            self.error_message = error.message or "E-mail ou senha incorretos."
        except XanoConfigurationError as error:
            self.clear_session()
            logger.error("Xano login configuration failure setting=XANO_API_URL reason=%s", error.reason)
            if error.reason == "missing":
                self.error_message = (
                    "XANO_API_URL não está configurada. Crie `.env` na raiz do projeto, "
                    "copie o modelo de `.env.example`, informe a URL base do grupo Xano "
                    "e reinicie o backend."
                )
            else:
                self.error_message = (
                    "XANO_API_URL inválida. Use uma URL base HTTP(S) do grupo Xano, "
                    "por exemplo https://<workspace>.xano.io/api:<grupo>."
                )
        except XanoMalformedResponseError as error:
            self.clear_session()
            safe_endpoint = _safe_xano_endpoint(endpoint)
            logger.error(
                "Xano login malformed response endpoint=%s status=%s",
                safe_endpoint,
                error.status_code,
            )
            self.error_message = (
                "O Xano respondeu, mas os dados de autenticação estão inválidos. "
                "Confira os endpoints /auth/login e /auth/me no grupo configurado."
            )
        except XanoAPIError as error:
            self.clear_session()
            safe_endpoint = _safe_xano_endpoint(endpoint)
            logger.error(
                "Xano login HTTP failure endpoint=%s status=%s",
                safe_endpoint,
                error.status_code,
            )
            if phase == "login" and error.status_code in {400, 401, 403}:
                self.error_message = error.message or "E-mail ou senha incorretos."
            else:
                self.error_message = (
                    f"O Xano respondeu com erro HTTP {error.status_code} em "
                    f"{urlsplit(safe_endpoint).path or '/auth/login'}. "
                    "Confira a URL base, o grupo e a publicação desse endpoint."
                )
        except requests.RequestException as error:
            self.clear_session()
            safe_endpoint = _safe_xano_endpoint(endpoint) if endpoint else "<XANO_API_URL>"
            logger.warning(
                "Xano login transport failure endpoint=%s exception=%s",
                safe_endpoint,
                type(error).__name__,
            )
            self.error_message = connection_error
        except (RuntimeError, ValueError) as error:
            self.clear_session()
            safe_endpoint = _safe_xano_endpoint(endpoint) if endpoint else "<XANO_API_URL>"
            logger.error(
                "Xano login unexpected failure endpoint=%s category=%s",
                safe_endpoint,
                type(error).__name__,
            )
            self.error_message = (
                "Não foi possível processar a resposta do Xano. "
                "Confira a configuração do endpoint e os logs do servidor."
            )
        finally:
            self.password = ""
            self.is_loading = False
        if redirect_event is not None:
            yield redirect_event

    def set_user_full_name(self, value: str) -> None:
        self.user_full_name = value

    def set_user_email(self, value: str) -> None:
        self.user_email = value

    def set_user_phone(self, value: str) -> None:
        self.user_phone = format_phone(value)

    def set_user_cpf(self, value: str) -> None:
        self.user_cpf = format_cpf(value)

    def set_profile_photo(self, value: str) -> None:
        self.user_profile_photo = value.strip()

    def load_profile(self) -> None:
        """Load the current user's profile without exposing auth data."""
        if not self.auth_token:
            return
        api_url = self.get_xano_api_url()
        if not api_url:
            self.profile_error = "O perfil ainda não está configurado neste ambiente."
            return
        self.profile_error = ""
        try:
            profile = fetch_user_profile(self.auth_token, api_url)
            self.profile_exists = bool(profile)
            self.user_full_name = profile.get("nome_completo") or self.user_full_name
            self.user_cpf = format_cpf(profile.get("cpf", ""))
            self.user_phone = format_phone(profile.get("telefone", ""))
            self.user_profile_photo = profile.get("foto_perfil") or self.user_profile_photo
            self.selected_profile_uploaded_url = ""
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 401:
                return self.expire_session()
            self.profile_error = "Não foi possível carregar seu perfil. Tente novamente."
        except requests.RequestException:
            self.profile_error = "Não foi possível carregar seu perfil. Tente novamente."
        except ValueError:
            self.profile_error = "O perfil retornado pelo Xano é inválido."

    def save_profile(self) -> None:
        """Create or update only the profile owned by the current token."""
        if self.profile_is_loading:
            return
        self.profile_error = ""
        self.profile_message = ""
        full_name = str(self.user_full_name or "").strip()
        cpf = digits_only(self.user_cpf)
        phone = digits_only(self.user_phone)
        if full_name == "":
            self.profile_error = "Informe seu nome completo."
            return
        if cpf and len(cpf) != 11:
            self.profile_error = "Informe um CPF válido."
            return
        if phone and len(phone) not in {10, 11}:
            self.profile_error = "Informe um telefone válido."
            return
        if not self.auth_token:
            self.profile_error = "Sua sessão expirou. Entre novamente."
            return
        api_url = self.get_xano_api_url()
        if not api_url:
            self.profile_error = "O perfil ainda não está configurado neste ambiente."
            return
        self.profile_is_loading = True
        profile_file = None
        if self.selected_profile_image and not self.selected_profile_uploaded_url:
            try:
                metadata, encoded = self.selected_profile_image.split(",", 1)
                mime_type = metadata.removeprefix("data:").removesuffix(";base64")
                if mime_type not in {"image/jpeg", "image/png"}:
                    raise ValueError("Unsupported profile image type")
                file_content = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error):
                self.profile_is_loading = False
                self.profile_error = "Não foi possível carregar a imagem selecionada."
                return

            extension = ".jpg" if mime_type == "image/jpeg" else ".png"
            file_name = (self.selected_profile_filename or "").replace("\\", "/").rsplit("/", 1)[-1]
            if not file_name:
                file_name = f"profile-{self.user_id or 'user'}{extension}"
            elif not file_name.lower().endswith(extension):
                file_name = f"{file_name.rsplit('.', 1)[0]}{extension}"
            profile_file = {
                "field_name": "foto_perfil",
                "name": file_name,
                "content": file_content,
                "mime_type": mime_type,
            }

        try:
            if profile_file:
                self.selected_profile_uploaded_url = upload_user_profile_photo(
                    self.auth_token,
                    api_url,
                    profile_file,
                )

            photo_value = (
                self.selected_profile_uploaded_url
                if self.selected_profile_image
                else str(self.user_profile_photo or "").strip()
            )
            payload = {
                "nome_completo": full_name,
                "cpf": cpf,
                "telefone": phone,
                "foto_perfil": photo_value,
            }
            profile = save_user_profile(
                self.auth_token,
                api_url,
                payload,
                "PUT" if self.profile_exists else "POST",
            )
            self.profile_exists = True
            self.user_full_name = str(profile.get("nome_completo") or full_name)
            self.user_cpf = format_cpf(str(profile.get("cpf") or cpf))
            self.user_phone = format_phone(str(profile.get("telefone") or phone))
            self.user_profile_photo = profile.get("foto_perfil") or photo_value or self.user_profile_photo
            self.selected_profile_image = ""
            self.selected_profile_filename = ""
            self.selected_profile_uploaded_url = ""
            self.profile_message = "Dados atualizados com sucesso."
        except XanoAPIError as error:
            if error.status_code == 401:
                return self.expire_session()
            self.profile_error = error.message
        except requests.RequestException:
            self.profile_error = "Não foi possível salvar seu perfil. Tente novamente."
        except ValueError:
            self.profile_error = "O perfil retornado pelo Xano é inválido."
        finally:
            self.profile_is_loading = False

    def handle_profile_upload(self, files: list[rx.UploadFile]):
        """Store a local image preview and keep it ready for the profile save payload."""
        if not files:
            return

        uploaded_file = files[0]
        file_like = getattr(uploaded_file, "file", None)
        if file_like is None:
            return

        try:
            file_like.seek(0)
            contents = file_like.read()
            if not isinstance(contents, bytes) or not contents:
                raise ValueError("The selected file is empty or unreadable")
            file_name = getattr(uploaded_file, "name", None) or "profile-image"
            file_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
            data_url = build_image_data_url(file_name, contents)
            self.selected_profile_image = data_url
            self.selected_profile_filename = file_name
            self.selected_profile_uploaded_url = ""
            self.profile_error = ""
        except (OSError, ValueError):
            self.profile_error = "Não foi possível carregar a imagem selecionada."


AppState = AuthState



class OperationalState(rx.State):
    """Operational state for map and service requests."""

    # Mock Data for Providers
    providers: list[dict] = [
        {"id": 1, "name": "João Socorro", "coords": [-23.5505, -46.6333], "specialties": ["tire", "battery"], "status": "online"},
        {"id": 2, "name": "Maria Assist", "coords": [-23.5550, -46.6350], "specialties": ["mechanical", "fuel"], "status": "online"},
        {"id": 3, "name": "SOS Rapidão", "coords": [-23.5450, -46.6300], "specialties": ["tire", "mechanical"], "status": "offline"},
        {"id": 4, "name": "Carlos Guincho", "coords": [-23.5600, -46.6400], "specialties": ["mechanical", "fuel"], "status": "online"},
    ]

    # Real-time tracking data
    # { provider_id: {"lat": float, "lng": float, "timestamp": float} }
    provider_locations: dict[int, dict] = {}
    client_location: dict[str, float] = {"lat": 0.0, "lng": 0.0}
    lat_lng_update_value: str = ""

    # Mock Data for Active Calls
    active_calls: list[dict] = [
        {"id": 101, "service_type": "Pneu Furado", "coords": [-23.5520, -46.6340], "status": "pending"},
        {"id": 102, "service_type": "Bateria", "coords": [-23.5580, -46.6310], "status": "pending"},
    ]
    is_available: bool = True
    available_requests: list[dict] = []
    selected_request: dict = {}
    atendimento_mock: dict = {}
    atendimento_phase: str = ""
    show_cancel_confirm: bool = False
    service_messages: list[dict] = []
    active_message_request_id: int | None = None
    message_poll_generation: int = 0
    message_sync_status: str = ""
    message_draft: str = ""
    message_error: str = ""
    show_message_panel: bool = False
    client_message_draft: str = ""
    client_message_error: str = ""
    show_client_message_panel: bool = False


    # Customer Request state
    selected_service: str | None = None
    request_status: str = "idle" # idle, searching, matched
    selected_vehicle_id: int | None = None
    selected_vehicle_option: str = ""
    pending_service_type: str = ""
    request_id: int | None = None
    request_server_status: str = ""
    request_estimated_price: float = 0.0
    request_distance_km: float = 0.0
    request_error_message: str = ""
    show_profile_link: bool = False
    show_vehicle_selection: bool = False

    # Provider identity (simulated)
    current_provider_id: int = 1
    current_provider_specialties: list[str] = ["tire", "battery"]
    user_vehicles: list[dict] = [
        {"id": 1, "brand": "Toyota", "model": "Corolla", "plate": "ABC-1234", "year": 2020, "color": "Prata"},
    ]
    # Modal state for vehicles
    show_vehicle_modal: bool = False
    editing_vehicle_id: int | None = None
    v_brand: str = ""
    v_model: str = ""
    v_plate: str = ""
    v_year: int = 2024
    v_color: str = ""

    async def _get_auth_token(self) -> str:
        auth_state = await self.get_state(AuthState)
        return auth_state.auth_token

    @rx.var
    def vehicle_options(self) -> list[str]:
        """Return vehicle IDs as select options for the request sheet."""
        return [str(vehicle.get("id", "")) for vehicle in self.user_vehicles]

    @rx.var
    def request_price_text(self) -> str:
        """Format the estimated price for the request confirmation."""
        return f"R$ {self.request_estimated_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def request_distance_text(self) -> str:
        """Format the estimated distance for the request confirmation."""
        return f"{self.request_distance_km:.1f}".replace(".", ",") + " km"

    def add_vehicle(self, brand: str, model: str, plate: str, year: int, color: str):
        """Add a new vehicle to the local mock list."""
        new_id = max([v["id"] for v in self.user_vehicles], default=0) + 1
        self.user_vehicles.append({
            "id": new_id,
            "brand": brand,
            "model": model,
            "plate": plate,
            "year": year,
            "color": color,
        })
        self.user_vehicles = self.user_vehicles # Trigger state update

    def update_vehicle(self, vehicle_id: int, brand: str, model: str, plate: str, year: int, color: str):
        """Update an existing vehicle in the local mock list."""
        for v in self.user_vehicles:
            if v["id"] == vehicle_id:
                v.update({"brand": brand, "model": model, "plate": plate, "year": year, "color": color})
        self.user_vehicles = self.user_vehicles # Trigger state update

    def set_v_brand(self, v: str):
        self.v_brand = v

    def set_v_model(self, v: str):
        self.v_model = v

    def set_v_plate(self, v: str):
        self.v_plate = v

    def set_v_year(self, v: str):
        try:
            self.v_year = int(v)
        except ValueError:
            pass

    def set_v_color(self, v: str):
        self.v_color = v

    def delete_vehicle(self, vehicle_id: int):
        """Remove a vehicle from the local mock list."""
        self.user_vehicles = [v for v in self.user_vehicles if v["id"] != vehicle_id]

    def open_vehicle_modal(self, vehicle_id: int | None = None):
        """Open modal for creating or editing a vehicle."""
        self.show_vehicle_modal = True
        self.editing_vehicle_id = vehicle_id
        if vehicle_id:
            v = next((v for v in self.user_vehicles if v["id"] == vehicle_id), None)
            if v:
                self.v_brand = v["brand"]
                self.v_model = v["model"]
                self.v_plate = v["plate"]
                self.v_year = v["year"]
                self.v_color = v["color"]
        else:
            self.v_brand = ""
            self.v_model = ""
            self.v_plate = ""
            self.v_year = 2024
            self.v_color = ""

    def open_new_vehicle_modal(self):
        """Open the vehicle form for a new vehicle."""
        self.open_vehicle_modal()

    def close_vehicle_modal(self):
        self.show_vehicle_modal = False
        self.editing_vehicle_id = None

    async def save_vehicle(self):
        """Save a vehicle through Xano and refresh the profile list."""
        if not self.v_plate or not self.v_brand or not self.v_model:
            return rx.toast("Preencha marca, modelo e placa.")

        token = await self._get_auth_token()
        if not isinstance(token, str) or not token.strip():
            return AuthState.expire_session()

        api_url = get_xano_services_url()
        payload = {
            "brand": self.v_brand,
            "model": self.v_model,
            "plate": self.v_plate,
            "year": int(self.v_year) if str(self.v_year).isdigit() else 2024,
            "color": self.v_color,
        }
        try:
            response = requests.post(
                f"{api_url}/vehicles",
                json=payload,
                headers=_auth_headers(token),
                timeout=10,
            )
            if response.status_code >= 400:
                raise XanoAPIError(response.status_code, _response_message(response))
            await self.load_user_vehicles()
            self.close_vehicle_modal()
            return rx.toast("Veículo cadastrado com sucesso!")
        except XanoAPIError as error:
            logger.error("Failed to save vehicle status=%s error=%s", error.status_code, error.message)
            if error.status_code == 401:
                return AuthState.expire_session()
            return rx.toast("Não foi possível salvar o veículo. Tente novamente.")
        except Exception as error:
            logger.exception("Failed to save vehicle: %s", error)
            return rx.toast("Não foi possível salvar o veículo. Tente novamente.")

    async def load_user_vehicles(self):
        """Load the authenticated user's vehicles without blocking the profile."""
        token = await self._get_auth_token()
        if not isinstance(token, str) or not token.strip():
            self.user_vehicles = []
            return

        try:
            self.user_vehicles = fetch_user_vehicles_xano(token, get_xano_services_url())
        except XanoAPIError as error:
            logger.error("Failed to load user vehicles status=%s error=%s", error.status_code, error.message)
            self.user_vehicles = []
            if error.status_code == 401:
                return AuthState.expire_session()
        except Exception as error:
            logger.exception("Failed to load user vehicles: %s", error)
            self.user_vehicles = []


    def toggle_provider_status(self):
        """Toggle status of the current simulated provider."""
        self.is_available = not self.is_available
        for p in self.providers:
            if p["id"] == self.current_provider_id:
                p["status"] = "online" if self.is_available else "offline"
        self.providers = list(self.providers)

    def _map_xano_to_ui_request(self, xano_req: dict) -> dict:
        """Convert a Xano request object to the UI format expected by available_requests."""
        service_type = xano_req.get("service_type", "other")

        # Mapping service types to friendly names and icons
        type_map = {
            "tire": ("Troca de Pneu", "🛞"),
            "battery": ("Bateria", "🔋"),
            "mechanical": ("Mecânica", "🔧"),
            "fuel": ("Combustível", "⛽"),
            "other": ("Outro Problema", "🛠️"),
        }
        friendly_name, icon = type_map.get(service_type, ("Solicitação", "🛠️"))

        # Calculate distance from provider's current location
        provider_lat = self.provider_locations.get(self.current_provider_id, {}).get("lat", self.providers[0]["coords"][0] if self.providers else -23.55)
        provider_lng = self.provider_locations.get(self.current_provider_id, {}).get("lng", self.providers[0]["coords"][1] if self.providers else -46.63)
        req_lat = xano_req.get("latitude", 0.0)
        req_lng = xano_req.get("longitude", 0.0)

        dist_km = self._haversine(provider_lat, provider_lng, req_lat, req_lng)

        # Construct Google Maps URL
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={req_lat},{req_lng}"
        user_record = xano_req.get("_user") or xano_req.get("user") or {}
        vehicle_record = xano_req.get("_vehicle") or xano_req.get("vehicle") or {}
        vehicle_details = xano_req.get("vehicle_details") or vehicle_record.get("details")
        if not vehicle_details and vehicle_record:
            vehicle_details = " ".join(
                str(vehicle_record.get(field, "")).strip()
                for field in ("brand", "model", "plate")
                if vehicle_record.get(field)
            )

        return {
            "id": xano_req.get("id"),
            "type": friendly_name,
            "service_icon": icon,
            "user": user_record.get("name") or xano_req.get("user_name") or xano_req.get("name") or "Usuário",
            "phone": format_phone(user_record.get("phone") or xano_req.get("user_phone") or xano_req.get("phone") or ""),
            "vehicle": vehicle_details or "Veículo não informado",
            "note": xano_req.get("note") or "Sem observações.",
            "distance": f"{dist_km:.1f} km",
            "eta": f"{int(dist_km * 3 + 5)} min", # Simple mock ETA based on distance
            "address": xano_req.get("address") or "Endereço não informado",
            "coords": [req_lat, req_lng],
            "maps_url": maps_url,
        }

    @rx.event(background=True)
    async def poll_pending_requests(self):
        """Background task that fetches real pending requests from Xano every 20 seconds."""
        while True:
            async with self:
                token = await self._get_auth_token()
                if not token:
                    logger.warning("Polling skipped: No auth token available")
                    await asyncio.sleep(10)
                    continue

                try:
                    logger.info("Polling pending requests from Xano...")
                    raw_requests = fetch_pending_requests_xano(token, get_xano_services_url())
                    mapped_requests = [self._map_xano_to_ui_request(r) for r in raw_requests]
                    self.available_requests = mapped_requests
                    logger.info("Successfully polled %s pending requests from Xano", len(mapped_requests))
                except Exception as e:
                    logger.error("Failed to poll pending requests: %s", e)

            await asyncio.sleep(20)

    def refresh_available_requests(self):
        """Now handled by background polling, but kept for compatibility."""
        pass


    async def accept_request(self, request_id: int):
        """Select a request, update status in Xano, and start attendance flow."""
        # DIAGNOSTIC LOG: Check what ID is actually being passed to the function
        logger.info("--- ACCEPT REQUEST ATTEMPT ---")
        logger.info("Request ID received from frontend: %s", request_id)

        request = next((item for item in self.available_requests if item["id"] == request_id), None)
        if request is None:
            logger.warning("Request ID %s not found in available_requests list", request_id)
            return rx.toast("Solicitação não encontrada na lista local.")

        token = await self._get_auth_token()
        if not token:
            logger.error("No auth token available for accept_request")
            return AuthState.expire_session()

        try:
            logger.info("Attempting to update Xano status for ID %s to 'accepted'...", request_id)
            accept_service_request_xano(
                auth_token=token,
                api_url=get_xano_services_url(),
                request_id=request_id,
            )
            logger.info("Successfully updated status in Xano for ID %s", request_id)
        except XanoAPIError as error:
            logger.error("Xano API Error during accept_request: status=%s", error.status_code)
            if error.status_code == 401:
                return AuthState.expire_session()
            if error.status_code == 404:
                return rx.toast("Este chamado não está mais disponível.")
            if error.status_code == 400:
                return rx.toast("Os dados do chamado são inválidos.")
            return rx.toast("Não foi possível aceitar o chamado. Tente novamente.")
        except Exception as error:
            logger.exception("Unexpected error accepting request %s: %s", request_id, error)
            return rx.toast("Ocorreu um erro inesperado ao processar a aceitação.")

        self.selected_request = request

        # IMPORTANT: We use the selected_request data to populate the atendimento_mock
        provider = next((item for item in self.providers if item["id"] == self.current_provider_id), None)
        provider_coords = provider["coords"] if provider else [-23.5505, -46.6333]

        self.atendimento_mock = build_atendimento_mock(request, provider_coords)
        self.atendimento_phase = "A_CAMINHO"
        self.show_cancel_confirm = False
        self.available_requests = [item for item in self.available_requests if item["id"] != request_id]

        logger.info("Request %s accepted and redirected to progress screen", request_id)
        return rx.redirect("/provider-service-progress")

    def refuse_request(self, request_id: int):
        """Remove a request from the provider's local queue."""
        self.available_requests = [item for item in self.available_requests if item["id"] != request_id]
        return rx.toast("Solicitação recusada.")

    def reset_provider_home(self):
        """Restore the provider home presentation after returning from details."""
        self.is_available = True
        self.selected_request = {}

    def reset_atendimento(self):
        """Clear current attendance local/mock data."""
        self.selected_request = {}
        self.atendimento_mock = {}
        self.atendimento_phase = ""
        self.show_cancel_confirm = False

    @rx.var
    def atendimento_next_action_label(self) -> str:
        """Return the main CTA label based on current attendance phase."""
        if self.atendimento_phase == "A_CAMINHO":
            return "Cheguei ao local"
        if self.atendimento_phase == "NO_LOCAL":
            return "Iniciar atendimento"
        if self.atendimento_phase == "ATENDENDO":
            return "Concluir atendimento"
        return "Atendimento concluído"

    @rx.var
    def atendimento_status_text(self) -> str:
        """Human readable attendance phase label."""
        if self.atendimento_phase == "A_CAMINHO":
            return "A caminho"
        if self.atendimento_phase == "NO_LOCAL":
            return "No local"
        if self.atendimento_phase == "ATENDENDO":
            return "Atendendo"
        if self.atendimento_phase == "CONCLUIDO":
            return "Concluído"
        return "Sem atendimento"

    @rx.var
    def can_cancel_atendimento(self) -> bool:
        """Allow cancellation only in first phases."""
        return self.atendimento_phase in ["A_CAMINHO", "NO_LOCAL"]

    @rx.var
    def atendimento_provider_coords(self) -> list[float]:
        """Provider coordinates for the current attendance map route."""
        return self.atendimento_mock.get("provider_coords", [-23.5505, -46.6333])

    @rx.var
    def atendimento_user_coords(self) -> list[float]:
        """User coordinates for the current attendance map route."""
        return self.atendimento_mock.get("user_coords", [-23.5614, -46.6559])

    @rx.var
    def atendimento_route_script(self) -> str:
        """Script that initializes map and renders the current route."""
        provider = self.atendimento_provider_coords
        user = self.atendimento_user_coords
        return (
            "window.initSOSMap('provider-service-progress-map', "
            f"[{provider[0]}, {provider[1]}], 13);"
            "window.showSOSRoute('provider-service-progress-map', "
            f"[{provider[0]}, {provider[1]}], "
            f"[{user[0]}, {user[1]}]);"
        )

    def open_cancel_confirm(self):
        """Open cancellation confirmation modal."""
        self.show_cancel_confirm = True

    def close_cancel_confirm(self):
        """Close cancellation confirmation modal."""
        self.show_cancel_confirm = False

    async def confirm_cancel_atendimento(self):
        """Cancel attendance, revert status to pending in Xano, and return to provider home."""
        request_id = self.atendimento_mock.get("id")
        token = await self._get_auth_token()

        if request_id and token:
            try:
                # Revert status to 'pending' so other providers can see it again
                release_service_request_xano(
                    auth_token=token,
                    api_url=get_xano_services_url(),
                    request_id=request_id,
                )
            except Exception as error:
                logger.error("Failed to revert request status to pending: %s", error)
                # We continue with local cleanup even if API fails to avoid locking the UI,
                # but in a production app we might want to warn the user.

        self.reset_atendimento()
        return rx.redirect("/home_provider")

    async def advance_atendimento_phase(self):
        """Advance through mock attendance phases in strict sequence."""
        request_id = self.atendimento_mock.get("id")
        token = await self._get_auth_token()

        if self.atendimento_phase == "A_CAMINHO":
            self.atendimento_phase = "NO_LOCAL"
            return
        if self.atendimento_phase == "NO_LOCAL":
            self.atendimento_phase = "ATENDENDO"
            return
        if self.atendimento_phase == "ATENDENDO":
            self.atendimento_phase = "CONCLUIDO"
            if request_id and token:
                try:
                    complete_service_request_xano(
                        auth_token=token,
                        api_url=get_xano_services_url(),
                        request_id=request_id,
                    )
                except Exception as error:
                    logger.error("Failed to update status to completed: %s", error)
            return rx.redirect("/service-finalized")

    def finish_atendimento_and_back_home(self):
        """Leave finalization screen and return to provider home."""
        self.reset_atendimento()
        return rx.redirect("/home_provider")

    def update_provider_location(self, provider_id: int, lat: float, lng: float):
        """Update a provider's real-time location."""
        self.provider_locations[provider_id] = {
            "lat": lat,
            "lng": lng,
            "timestamp": time.time(),
        }
        # Update the mock list for consistency
        for p in self.providers:
            if p["id"] == provider_id:
                p["coords"] = [lat, lng]

        self.provider_locations = self.provider_locations
        self.providers = self.providers

    def update_client_location(self, lat: float, lng: float):
        """Update the client's real-time location."""
        self.client_location = {"lat": lat, "lng": lng}

    def handle_lat_lng_update(self, value: str):
        """Handle location updates from the JS bridge via a hidden input."""
        import json
        try:
            data = json.loads(value)
            lat = data.get("lat")
            lng = data.get("lng")
            role = data.get("role")
            provider_id = data.get("provider_id")

            if role == "client":
                self.update_client_location(lat, lng)
            elif role == "provider" and provider_id is not None:
                self.update_provider_location(provider_id, lat, lng)
        except Exception as e:
            print(f"Error parsing location update: {e}")
        finally:
            self.lat_lng_update_value = "" # Clear to allow same-value updates

    @rx.var
    def client_center(self) -> list[float]:
        """Return client location as a list for Leaflet center."""
        return [self.client_location["lat"], self.client_location["lng"]]

    @rx.var
    def nearby_providers(self) -> list[dict]:
        """Return providers within a 5km radius of the client."""
        if self.client_location["lat"] == 0.0:
            return []

        nearby = []
        for p in self.providers:
            if p["status"] == "online":
                # Use real-time location if available, otherwise use mock coords
                coords = self.provider_locations.get(p["id"], {}).get("coords", p["coords"])
                # Wait, I stored them as lat/lng keys in provider_locations
                loc = self.provider_locations.get(p["id"], {})
                lat = loc.get("lat", p["coords"][0])
                lng = loc.get("lng", p["coords"][1])

                dist = self._haversine(
                    self.client_location["lat"], self.client_location["lng"],
                    lat, lng
                )
                if dist <= 5.0:
                    nearby.append({**p, "distance": round(dist, 2), "lat": lat, "lng": lng})

        return sorted(nearby, key=lambda x: x["distance"])

    async def notify_arrival(self):
        """Notify the client that the provider has arrived at the location."""
        request_id = self.atendimento_mock.get("id")
        token = await self._get_auth_token()

        if not request_id or not token:
            return rx.toast("Erro: Dados de atendimento insuficientes.")

        try:
            send_service_message_xano(
                auth_token=token,
                api_url=get_xano_services_url(),
                request_id=request_id,
                message_text="Cheguei ao local!"
            )
            return rx.toast("Cliente notificado da sua chegada!")
        except Exception as error:
            logger.error("Failed to send arrival notification category=%s", type(error).__name__)
            return rx.toast("Erro ao enviar notificação. Tente novamente.")

    async def open_message_panel(self):
        """Open the conversation panel and load the current messages."""
        self.message_error = ""
        self.message_sync_status = "Atualização automática ativa."
        self.service_messages = []
        request_id = self.atendimento_mock.get("id")
        self.active_message_request_id = int(request_id) if request_id is not None else None
        self.show_message_panel = True
        await self.load_service_messages()

    def close_message_panel(self):
        self.show_message_panel = False
        self.message_error = ""
        self.message_sync_status = ""
        self.active_message_request_id = None
        self.message_poll_generation += 1

    def set_message_draft(self, value: str):
        self.message_draft = value

    async def load_service_messages(self):
        """Load the current service request conversation from Xano."""
        request_id = self.atendimento_mock.get("id")
        token = await self._get_auth_token()
        if not request_id or not token:
            self.message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Sessão ou chamado indisponível."
            return

        try:
            self.service_messages = await asyncio.to_thread(
                fetch_service_messages_xano,
                token,
                get_xano_services_url(),
                request_id,
            )
            self.message_sync_status = "Atualização automática ativa."
        except XanoAPIError as error:
            logger.error("Failed to load service messages status=%s", error.status_code)
            self.message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."
        except (requests.RequestException, ValueError) as error:
            logger.error("Failed to load service messages category=%s", type(error).__name__)
            self.message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."

    def _open_conversation_request_id(self) -> int | None:
        if self.show_message_panel:
            request_id = self.atendimento_mock.get("id")
        elif self.show_client_message_panel:
            request_id = self.request_id
        else:
            return None
        return int(request_id) if request_id is not None else None

    async def refresh_open_service_messages(self, expected_request_id: int) -> bool:
        """Refresh the open conversation without dropping messages on transient failures."""
        async with self:
            if (
                self._open_conversation_request_id() != expected_request_id
                or self.active_message_request_id != expected_request_id
            ):
                return False
            token = await self._get_auth_token()
        if not token:
            async with self:
                if (
                    self._open_conversation_request_id() == expected_request_id
                    and self.active_message_request_id == expected_request_id
                ):
                    self.message_sync_status = "Sessão indisponível. Entre novamente para continuar."
            return False

        try:
            refreshed_messages = await asyncio.to_thread(
                fetch_service_messages_xano,
                token,
                get_xano_services_url(),
                expected_request_id,
            )
        except XanoAPIError as error:
            logger.error("Failed to refresh service messages status=%s", error.status_code)
            async with self:
                if (
                    self._open_conversation_request_id() == expected_request_id
                    and self.active_message_request_id == expected_request_id
                ):
                    self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."
            return False
        except (requests.RequestException, ValueError) as error:
            logger.error("Failed to refresh service messages category=%s", type(error).__name__)
            async with self:
                if (
                    self._open_conversation_request_id() == expected_request_id
                    and self.active_message_request_id == expected_request_id
                ):
                    self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."
            return False

        async with self:
            if (
                self._open_conversation_request_id() != expected_request_id
                or self.active_message_request_id != expected_request_id
            ):
                return False

            self.service_messages = refreshed_messages
            self.message_sync_status = "Atualização automática ativa."
        return True

    @rx.event(background=True)
    async def poll_service_messages(self):
        """Refresh the open conversation every two seconds while its panel is visible."""
        async with self:
            self.message_poll_generation += 1
            generation = self.message_poll_generation
            request_id = self._open_conversation_request_id()
            if request_id is None or request_id != self.active_message_request_id:
                return

        while True:
            await asyncio.sleep(2)
            async with self:
                if (
                    generation != self.message_poll_generation
                    or self._open_conversation_request_id() != request_id
                    or self.active_message_request_id != request_id
                ):
                    return
            await self.refresh_open_service_messages(request_id)

    async def send_message(self):
        """Send the drafted message and append the created record locally."""
        message_text = self.message_draft.strip()
        request_id = self.atendimento_mock.get("id")
        token = await self._get_auth_token()
        if not message_text:
            self.message_error = "Digite uma mensagem."
            return
        if not request_id or not token:
            self.message_error = "Não foi possível enviar a mensagem."
            return

        try:
            message = await asyncio.to_thread(
                send_service_message_xano,
                token,
                get_xano_services_url(),
                request_id,
                message_text,
            )
            self.service_messages = [*self.service_messages, message]
            self.message_draft = ""
            self.message_error = ""
        except XanoAPIError as error:
            logger.error("Failed to send service message status=%s", error.status_code)
            self.message_error = "Não foi possível enviar a mensagem."
        except (requests.RequestException, ValueError) as error:
            logger.error("Failed to send service message category=%s", type(error).__name__)
            self.message_error = "Não foi possível enviar a mensagem."

    async def open_client_message_panel(self):
        """Open the client conversation for the active request."""
        self.client_message_error = ""
        self.message_sync_status = "Atualização automática ativa."
        self.service_messages = []
        self.active_message_request_id = (
            int(self.request_id) if self.request_id is not None else None
        )
        self.show_client_message_panel = True
        await self.load_client_service_messages()

    def close_client_message_panel(self):
        self.show_client_message_panel = False
        self.client_message_error = ""
        self.message_sync_status = ""
        self.active_message_request_id = None
        self.message_poll_generation += 1

    def set_client_message_draft(self, value: str):
        self.client_message_draft = value

    async def load_client_service_messages(self):
        """Load messages for the client's active request."""
        token = await self._get_auth_token()
        if self.request_id is None or not token:
            self.client_message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Sessão ou chamado indisponível."
            return

        try:
            self.service_messages = await asyncio.to_thread(
                fetch_service_messages_xano,
                token,
                get_xano_services_url(),
                self.request_id,
            )
            self.message_sync_status = "Atualização automática ativa."
        except XanoAPIError as error:
            logger.error("Failed to load client messages status=%s", error.status_code)
            self.client_message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."
        except (requests.RequestException, ValueError) as error:
            logger.error("Failed to load client messages category=%s", type(error).__name__)
            self.client_message_error = "Não foi possível carregar as mensagens."
            self.message_sync_status = "Conexão instável. Tentando novamente automaticamente."

    async def send_client_message(self):
        """Send a message from the client for the active request."""
        message_text = self.client_message_draft.strip()
        token = await self._get_auth_token()
        if not message_text:
            self.client_message_error = "Digite uma mensagem."
            return
        if self.request_id is None or not token:
            self.client_message_error = "Não foi possível enviar a mensagem."
            return

        try:
            message = await asyncio.to_thread(
                send_service_message_xano,
                token,
                get_xano_services_url(),
                self.request_id,
                message_text,
            )
            self.service_messages = [*self.service_messages, message]
            self.client_message_draft = ""
            self.client_message_error = ""
        except XanoAPIError as error:
            logger.error("Failed to send client message status=%s", error.status_code)
            self.client_message_error = "Não foi possível enviar a mensagem."
        except (requests.RequestException, ValueError) as error:
            logger.error("Failed to send client message category=%s", type(error).__name__)
            self.client_message_error = "Não foi possível enviar a mensagem."

    @rx.event(background=True)
    async def cleanup_stale_providers(self):
        """Background task to remove providers who haven't updated in 5 minutes."""
        while True:
            await asyncio.sleep(60)
            async with self:
                now = time.time()
                # Mark providers offline if no update for 300s
                for p in self.providers:
                    loc = self.provider_locations.get(p["id"], {})
                    if loc.get("timestamp", 0) < now - 300:
                        p["status"] = "offline"
                self.providers = self.providers


    @rx.event
    async def submit_customer_request(self, service_type: str):
        """Start a real service request through Xano."""
        return await self._submit_customer_request(service_type)

    async def _submit_customer_request(self, service_type: str):
        """Validate request inputs and call Xano without affecting other flows."""
        self.request_error_message = ""
        self.show_profile_link = False

        if not self.user_vehicles:
            self.request_status = "idle"
            self.request_error_message = "Cadastre um veículo no perfil antes de pedir socorro."
            self.show_profile_link = True
            return rx.toast(self.request_error_message)

        if self.selected_vehicle_id is None:
            if len(self.user_vehicles) == 1:
                self.selected_vehicle_id = self.user_vehicles[0].get("id")
                self.selected_vehicle_option = str(self.selected_vehicle_id)
            else:
                self.pending_service_type = service_type
                self.show_vehicle_selection = True
                return rx.toast("Selecione um veículo para continuar.")

        latitude = self.client_location.get("lat", 0.0)
        longitude = self.client_location.get("lng", 0.0)
        if not latitude or not longitude:
            self.request_status = "idle"
            self.request_error_message = "Ative sua localização antes de pedir socorro."
            return rx.toast(self.request_error_message)

        token = await self._get_auth_token()
        if not isinstance(token, str) or not token.strip():
            self.request_status = "idle"
            logger.warning("Service request skipped: authenticated token is unavailable")
            return AuthState.expire_session()

        self.selected_service = service_type
        self.request_status = "searching"
        try:
            result = request_service_xano(
                auth_token=token,
                api_url=get_xano_services_url(),
                service_type=service_type,
                vehicle_id=int(self.selected_vehicle_id),
                latitude=latitude,
                longitude=longitude,
            )
            self.request_id = result.get("request_id")
            self.request_server_status = str(result.get("status", ""))
            self.request_estimated_price = float(result.get("estimated_price", 0.0))
            self.request_distance_km = float(result.get("distance_km", 0.0))
            self.request_status = "searching"
            # Keep the request hidden from the provider queue while the customer is still
            # actively searching. Only real acceptance should expose it to providers.
            pending_provider_requests[:] = []
            return
        except XanoAPIError as error:
            logger.error(
                "Request service failed status=%s error=%s",
                error.status_code,
                error.message,
            )
            self.request_status = "idle"
            if error.status_code == 401:
                return AuthState.expire_session()
            elif error.status_code in {403, 404}:
                self.request_error_message = "O veículo selecionado não é válido. Escolha outro veículo."
            elif error.status_code == 400:
                self.request_error_message = "Os dados da solicitação são inválidos. Confira os dados e tente novamente."
            else:
                self.request_error_message = "Não foi possível processar sua solicitação."
            return rx.toast(self.request_error_message)
        except Exception as error:
            logger.exception("Request service failed: %s", error)
            self.request_status = "idle"
            self.request_error_message = "Não foi possível processar sua solicitação."
            return rx.toast(self.request_error_message)

    @rx.event
    def set_selected_vehicle_option(self, value: str):
        """Store the vehicle selected in the request sheet."""
        self.selected_vehicle_option = value
        try:
            self.selected_vehicle_id = int(value)
        except ValueError:
            self.selected_vehicle_id = None

    @rx.event
    async def confirm_vehicle_selection(self):
        """Confirm the selected vehicle and continue the pending request."""
        if self.selected_vehicle_id is None:
            return rx.toast("Selecione um veículo para continuar.")
        self.show_vehicle_selection = False
        service_type = self.pending_service_type
        self.pending_service_type = ""
        if service_type:
            return await self._submit_customer_request(service_type)

    @rx.event
    def open_profile_for_request(self):
        """Open the profile so the user can register a vehicle."""
        return rx.redirect("/profile")

    def _simulate_match(self):
        """Private method to simulate finding a provider."""
        self.request_status = "matched"

    def set_request_status(self, status: str):
        """Update the request status."""
        self.request_status = status

    def set_provider_name(self, name: str):
        """Update the name of the current simulated provider."""
        for p in self.providers:
            if p["id"] == self.current_provider_id:
                p["name"] = name
        self.providers = self.providers # Trigger state update

    def toggle_specialty(self, specialty: str):
        """Toggle a specialty for the current simulated provider."""
        if specialty in self.current_provider_specialties:
            self.current_provider_specialties.remove(specialty)
        else:
            self.current_provider_specialties.append(specialty)

        for p in self.providers:
            if p["id"] == self.current_provider_id:
                if specialty in p["specialties"]:
                    p["specialties"].remove(specialty)
                else:
                    p["specialties"].append(specialty)
        self.providers = self.providers # Trigger state update

    @rx.var
    def online_providers_count(self) -> int:
        """Return the number of providers who are currently online."""
        return len([p for p in self.providers if p["status"] == "online"])

    def accept_call(self, call_id: int):
        """Simulate a provider accepting a call."""
        for call in self.active_calls:
            if call["id"] == call_id:
                call["status"] = "accepted"
        self.active_calls = self.active_calls # Trigger state update

    def simulate_new_call(self):
        """Add a mock call for testing the provider dashboard."""
        import random
        services = ["Pneu Furado", "Bateria", "Mecânica", "Combustível"]
        new_call = {
            "id": random.randint(1000, 9999),
            "service_type": random.choice(services),
            "coords": [-23.55 + random.uniform(-0.01, 0.01), -46.63 + random.uniform(-0.01, 0.01)],
            "status": "pending"
        }
        self.active_calls.append(new_call)
        self.active_calls = self.active_calls # Trigger state update

def text_input(label: str, placeholder: str, value: str, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, class_name="field-label"),
        rx.input(
            value=value,
            placeholder=placeholder,
            on_change=on_change,
            width="100%",
            height="3.25rem",
            padding="0 1rem",
            border_radius="14px",
            border=f"1px solid {COLORS['line']}",
            background="white",
            color=COLORS["text"],
        ),
        width="100%",
        spacing="2",
    )


def profile_avatar() -> rx.Component:
    """Circular profile avatar that redirects to the profile page."""
    return rx.button(
        rx.cond(
            AppState.user_profile_photo != "",
            rx.image(
                src=AppState.user_profile_photo,
                width="100%",
                height="100%",
                border_radius="50%",
                object_fit="cover"
            ),
            rx.center(
                rx.text(
                    AppState.user_initials,
                    font_size="0.9rem",
                    weight="bold",
                    color=COLORS["text"]
                ),
                width="100%",
                height="100%",
                background=COLORS["line"],
                border_radius="50%",
            ),
        ),
        on_click=rx.redirect("/profile"),
        class_name="glass-panel",
        padding="0",
        border_radius="50%",
        width="2.8rem",
        height="2.8rem",
        cursor="pointer",
        overflow="hidden",
    )


def vehicle_card(v: dict) -> rx.Component:
    """Card for displaying a single vehicle."""
    return rx.hstack(
        rx.hstack(
            rx.vstack(
                rx.text(f"{v['brand']} {v['model']}", weight="bold", size="3"),
                rx.text(f"Placa: {v['plate']}", font_size="0.8rem", color=COLORS["text"]),
                align="start",
                spacing="1",
            ),
            width="100%",
            align="center",
            padding="1rem",
            background="white",
            border_radius="12px",
            border=f"1px solid {COLORS['line']}",
        ),
    )


def vehicle_modal() -> rx.Component:
    """Modal for adding or editing a vehicle."""
    return rx.cond(
        OperationalState.show_vehicle_modal,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.heading(
                        rx.cond(OperationalState.editing_vehicle_id, "Editar Veículo", "Adicionar Veículo"),
                        size="5",
                        margin_bottom="1rem",
                    ),
                    rx.vstack(
                        rx.text("Marca", class_name="field-label"),
                        rx.input(
                            value=OperationalState.v_brand,
                            on_change=OperationalState.set_v_brand,
                            width="100%",
                            border_radius="12px",
                        ),
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Modelo", class_name="field-label"),
                        rx.input(
                            value=OperationalState.v_model,
                            on_change=OperationalState.set_v_model,
                            width="100%",
                            border_radius="12px",
                        ),
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Placa", class_name="field-label"),
                        rx.input(
                            value=OperationalState.v_plate,
                            on_change=OperationalState.set_v_plate,
                            width="100%",
                            border_radius="12px",
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Ano", class_name="field-label"),
                            rx.input(
                                value=str(OperationalState.v_year),
                                on_change=OperationalState.set_v_year,
                                width="100%",
                                border_radius="12px",
                            ),
                            width="50%",
                        ),
                        rx.vstack(
                            rx.text("Cor", class_name="field-label"),
                            rx.input(
                                value=OperationalState.v_color,
                                on_change=OperationalState.set_v_color,
                                width="100%",
                                border_radius="12px",
                            ),
                            width="50%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button("Cancelar", on_click=OperationalState.close_vehicle_modal, class_name="secondary-button", width="100%"),
                        rx.button("Salvar", on_click=OperationalState.save_vehicle, class_name="primary-button", width="100%"),
                        spacing="3",
                        width="100%",
                        margin_top="1rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="2rem",
                background="white",
                border_radius="24px",
                width="min(100%, 24rem)",
                box_shadow="0 20px 50px rgba(0,0,0,0.2)",
            ),
            position="fixed",
            top="0",
            left="0",
            right="0",
                bottom="0",
            z_index="1000",
            background="rgba(0,0,0,0.5)",
            backdrop_filter="blur(4px)",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def brand_header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box("✦", class_name="brand-mark"),
            rx.text("SOS drive", class_name="brand-name"),
            spacing="3",
            align="center",
        ),
        rx.text("assistência que chega até você", class_name="top-pill"),
        justify="between",
        width="100%",
    )


def signup_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text("comece por aqui", class_name="section-kicker"),
            rx.heading("Crie sua conta.", class_name="section-title", size="8"),
            rx.text("Escolha como você quer usar a SOS Drive.", class_name="section-intro"),
            rx.hstack(
                rx.button(
                    rx.vstack(
                        rx.text("Cliente / Motorista", weight="bold"),
                        rx.text("Preciso de assistência", class_name="role-detail"),
                        spacing="1",
                        align="start",
                    ),
                        on_click=AppState.choose_signup_role("cliente"),
                    class_name=rx.cond(AppState.signup_role == "cliente", "role-card selected", "role-card"),
                    flex="1",
                ),
                rx.button(
                    rx.vstack(
                        rx.text("Prestador de serviço", weight="bold"),
                        rx.text("Ofereço assistência", class_name="role-detail"),
                        spacing="1",
                        align="start",
                    ),
                    on_click=AppState.choose_signup_role("prestador"),
                    class_name=rx.cond(AppState.signup_role == "prestador", "role-card selected", "role-card"),
                    flex="1",
                ),
                width="100%",
                spacing="3",
            ),
            rx.form(
                rx.vstack(
                    text_input("Nome", "Seu nome", AppState.signup_name, AppState.set_signup_name),
                    text_input("Email", "voce@exemplo.com", AppState.signup_email, AppState.set_signup_email),
                    rx.vstack(
                        rx.text("Senha", class_name="field-label"),
                        rx.input(
                            type="password",
                            placeholder="Crie uma senha",
                            value=AppState.signup_password,
                            on_change=AppState.set_signup_password,
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                            background="white",
                            color=COLORS["text"],
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    rx.button(
                        rx.cond(AuthState.is_loading, "Criando conta...", "Criar conta"),
                        type="submit",
                        class_name="primary-button",
                        width="100%",
                    ),
                    rx.cond(
                        AppState.error_message != "",
                        rx.text(AppState.error_message, class_name="error-message"),
                    ),
                    rx.cond(
                        AppState.signup_message != "",
                        rx.text(AppState.signup_message, class_name="success-message"),
                    ),
                    width="100%",
                    spacing="5",
                ),
                on_submit=AuthState.signup,
                width="100%",
            ),
            rx.button(
                "Já tenho uma conta",
                on_click=AppState.open_login,
                class_name="secondary-button",
            ),
            rx.button(
                "Voltar para apresentação",
                on_click=AppState.return_to_presentation,
                class_name="text-button",
            ),
            width="min(100%, 38rem)",
            align="start",
            spacing="5",
            class_name="login-panel",
        ),
        min_height="calc(100vh - 8rem)",
        padding="2rem 1rem",
    )


def login_screen() -> rx.Component:
    return rx.box(
        rx.el.video(
            src=LOGIN_BACKGROUND_VIDEO_URL,
            poster="/login-bg-fallback.svg",
            auto_play=True,
            loop=True,
            muted=True,
            plays_inline=True,
            aria_hidden="true",
            class_name="login-background-video",
        ),
        rx.box(class_name="login-background-overlay", aria_hidden="true"),
        rx.box(
            rx.vstack(
                rx.text("acesso seguro", class_name="section-kicker"),
                rx.heading("Entre para continuar.", class_name="section-title", size="8"),
                rx.text("Use seu email e senha para acessar a SOS Drive.", class_name="section-intro"),
                rx.form(
                    rx.vstack(
                        text_input("Email", "voce@exemplo.com", AppState.email, AppState.set_email_value),
                        rx.vstack(
                            rx.text("Senha", class_name="field-label"),
                            rx.input(
                                type="password",
                                placeholder="Sua senha",
                                value=AppState.password,
                                on_change=AppState.set_password_value,
                                width="100%",
                                height="3.25rem",
                                padding="0 1rem",
                                border_radius="14px",
                                border=f"1px solid {COLORS['line']}",
                                background="white",
                                color=COLORS["text"],
                            ),
                            width="100%",
                            spacing="2",
                        ),
                        rx.button(
                            rx.cond(AppState.is_loading, "Entrando...", "Entrar"),
                            type="submit",
                            class_name="primary-button",
                            width="100%",
                            disabled=AppState.is_loading,
                        ),
                        rx.cond(
                            AppState.error_message != "",
                            rx.text(AppState.error_message, class_name="error-message"),
                        ),
                        width="100%",
                        spacing="5",
                    ),
                    on_submit=AppState.login,
                    width="min(100%, 29rem)",
                ),
                rx.button(
                    "Voltar para apresentação",
                    on_click=AppState.return_to_presentation,
                    class_name="secondary-button",
                ),
                rx.button(
                    "Criar uma conta",
                    on_click=AppState.open_signup,
                    class_name="text-button",
                ),
                width="min(100%, 38rem)",
                align="start",
                spacing="5",
                class_name="login-panel login-background-card",
            ),
            class_name="login-content",
        ),
        class_name="login-page",
    )


def hero_visual() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("VISÃO EM TEMPO REAL", class_name="visual-label"),
                rx.hstack(
                    rx.text("●", color="#22C55E"),
                    rx.text("SISTEMA ATIVO", class_name="live-label", font_size="0.7rem", font_weight="bold"),
                    spacing="1",
                    align="center",
                ),
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.hstack(
                    rx.text("📍", font_size="1.2rem"),
                    rx.text("Sua localização atual", class_name="map-label"),
                    spacing="2",
                    align="center",
                ),
                class_name="map-preview",
            ),
            rx.hstack(
                rx.box("↗", class_name="assist-icon"),
                rx.vstack(
                    rx.text("Ajuda a caminho", weight="bold"),
                    rx.text("Especialista mais próximo · 12 min", class_name="assist-detail"),
                    align="start",
                    spacing="1",
                ),
                class_name="assist-card",
                width="100%",
            ),
            rx.text("3 profissionais disponíveis na sua região", class_name="mini-stats"),
            class_name="visual-content",
            width="100%",
        ),
        class_name="hero-visual",
        width="100%",
    )


def landing_page() -> rx.Component:
    steps = [
        ("01", "Conte o que aconteceu", "Escolha o tipo de problema com poucos toques e sem formulários longos."),
        ("02", "Encontre a melhor opção", "Veja profissionais disponíveis na região, com distância e estimativa de chegada."),
        ("03", "Acompanhe com clareza", "Saiba o que acontece em cada etapa até o atendimento ser concluído."),
    ]
    services = ["Pane mecânica", "Pneu furado", "Bateria", "Combustível", "Outro problema"]
    return rx.vstack(
        rx.box(
            brand_header(),
            rx.text("quando imprevistos acontecem", class_name="eyebrow"),
            rx.grid(
                rx.vstack(
                    rx.heading("Respire. A ajuda está chegando.", class_name="hero-title", size="9"),
                    rx.text(
                        "A SOS Drive encontra assistência confiável perto de você e transforma um momento difícil em um próximo passo simples.",
                        class_name="hero-copy",
                    ),
                    rx.hstack(
                        rx.text("◉ localização inteligente", class_name="trust-chip"),
                        rx.text("✓ profissionais verificados", class_name="trust-chip"),
                        rx.text("↗ acompanhamento claro", class_name="trust-chip"),
                        wrap="wrap",
                        spacing="3",
                    ),
                    rx.hstack(
                        rx.link(
                            "Conhecer a SOS Drive",
                            href="/login",
                            class_name="primary-button",
                            flex="1",
                            text_align="center",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            width="100%",
                        ),
                        rx.button("Ver mapa (Teste)", on_click=AppState.open_map_test, class_name="secondary-button", flex="1"),
                        width="100%",
                        spacing="3",
                        margin_top="1rem",
                    ),
                    align="start",
                    spacing="6",
                ),
                hero_visual(),
                columns="2",
                spacing="8",
                width="100%",
            ),
            class_name="hero-shell",
            width="100%",
        ),

        rx.text("uma jornada mais leve", class_name="section-kicker"),
        rx.heading("Do problema à solução, sem labirinto.", class_name="section-title", size="8"),
        rx.text(
            "Em poucos passos, você entende as opções disponíveis, escolhe o tipo de ajuda e acompanha tudo com mais tranquilidade.",
            class_name="section-intro",
        ),
        rx.grid(
            *[
                rx.box(
                    rx.text(f"{number} · simples assim", class_name="step-number"),
                    rx.heading(title, size="4"),
                    rx.text(copy),
                    class_name="info-card",
                )
                for number, title, copy in steps
            ],
            columns="3",
            spacing="4",
            width="100%",
        ),
        rx.text("assistência para o que você precisa", class_name="section-kicker"),
        rx.heading("Quando o carro para, você continua.", class_name="section-title", size="8"),
        rx.grid(
            *[rx.box(rx.text(service), class_name="service-card") for service in services],
            columns="5",
            spacing="3",
            width="100%",
        ),
        rx.box(
            rx.heading("Feita para momentos em que clareza importa.", size="5"),
            rx.text("24h · acesso quando precisar   |   1 lugar · para pedir e acompanhar   |   0 drama · menos etapas desnecessárias"),
            class_name="trust-band",
            width="100%",
        ),
        rx.text("Uma porta de entrada, não um labirinto.", class_name="bottom-note"),
        spacing="7",
        width="100%",
    )


def vehicle_selection_sheet() -> rx.Component:
    """Render the state-driven vehicle picker for a service request."""
    return rx.cond(
        OperationalState.show_vehicle_selection,
        rx.box(
            rx.vstack(
                rx.text("Selecione seu veículo", weight="bold", size="5", color=COLORS["navy"]),
                rx.text("Escolha qual veículo precisa de atendimento.", color=COLORS["text"]),
                rx.select(
                    OperationalState.vehicle_options,
                    value=OperationalState.selected_vehicle_option,
                    on_change=OperationalState.set_selected_vehicle_option,
                    placeholder="Escolha um veículo",
                    width="100%",
                ),
                rx.button(
                    "Confirmar veículo",
                    on_click=OperationalState.confirm_vehicle_selection,
                    class_name="primary-button",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            position="fixed",
            bottom="0",
            left="0",
            right="0",
            z_index="1000",
            padding="2rem 1rem",
            background="white",
            border_radius="24px 24px 0 0",
            box_shadow="0 -10px 30px rgba(0,0,0,0.15)",
        ),
    )


def customer_dashboard() -> rx.Component:
    return rx.box(
        # Map Container (Background)
        rx.box(
            id="customer-map",
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="0",
            on_mount=rx.call_script(
                "window.initSOSMap('customer-map', [-23.5505, -46.6333], 13);"
            ),
        ),
        vehicle_selection_sheet(),
        # Top Navigation Bar
        rx.hstack(
            rx.button(
                rx.text("🏠 Home"),
                on_click=rx.redirect("/home"),
                class_name="glass-panel",
                padding="0.5rem 1rem",
                border_radius="12px",
                font_size="0.8rem",
                weight="bold",
                cursor="pointer",
            ),
            rx.spacer(),
            profile_avatar(),
            position="absolute",
            top="2rem",
            left="2rem",
            right="2rem",
            z_index="100",
            pointer_events="auto",
            align="center",
        ),
        # Floating Status Pill
        rx.box(
            rx.hstack(
                rx.text("📡", font_size="1.2rem"),
                rx.text(
                    f"{OperationalState.online_providers_count} profissionais disponíveis agora",
                    weight="bold",
                    font_size="0.85rem",
                    color=COLORS["text"],
                    text_align="center",
                ),
                spacing="2",
                align="center",
                justify="center",
            ),
            class_name="glass-panel",
            padding="0.6rem 1.2rem",
            position="absolute",
            top="5.5rem",
            left="50%",
            transform="translateX(-50%)",
            z_index="50",
            width="auto",
            max_width="90%",
            pointer_events="auto",
            border_radius="999px",
        ),
        # Center Map Button
        rx.button(
            "🎯",
            on_click=rx.call_script("window.centerMap('customer-map')"),
            class_name="glass-panel",
            position="absolute",
            bottom="15rem",
            right="1rem",
            z_index="100",
            width="3rem",
            height="3rem",
            border_radius="50%",
            pointer_events="auto",
            cursor="pointer",
            font_size="1.5rem",
        ),
        # Bottom Sheet for Help Selection
        rx.vstack(
            # Bottom sheet handle
            rx.box(
                width="40px",
                height="4px",
                background=COLORS["line"],
                border_radius="2px",
                margin_bottom="1.5rem",
                align="center",
            ),
            rx.text("Do que você precisa?", weight="bold", size="6", margin_bottom="1rem", color=COLORS["text"], text_align="center"),
            rx.grid(
                rx.box(
                    rx.vstack(
                        rx.text("🚗", font_size="1.8rem"),
                        rx.text("Pneu Furado", font_size="0.8rem", color=COLORS["text"], weight="bold", text_align="center"),
                    ),
                    on_click=OperationalState.submit_customer_request("tire"),
                    class_name="op-card",
                    width="100%",
                    height="90px",
                    border_radius="16px",
                    cursor="pointer",
                    align="center",
                    justify="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("🔋", font_size="1.8rem"),
                        rx.text("Bateria", font_size="0.8rem", color=COLORS["text"], weight="bold", text_align="center"),
                    ),
                    on_click=OperationalState.submit_customer_request("battery"),
                    class_name="op-card",
                    width="100%",
                    height="90px",
                    border_radius="16px",
                    cursor="pointer",
                    align="center",
                    justify="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("🔧", font_size="1.8rem"),
                        rx.text("Mecânica", font_size="0.8rem", color=COLORS["text"], weight="bold", text_align="center"),
                    ),
                    on_click=OperationalState.submit_customer_request("mechanical"),
                    class_name="op-card",
                    width="100%",
                    height="90px",
                    border_radius="16px",
                    cursor="pointer",
                    align="center",
                    justify="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("⛽", font_size="1.8rem"),
                        rx.text("Combustível", font_size="0.8rem", color=COLORS["text"], weight="bold", text_align="center"),
                    ),
                    on_click=OperationalState.submit_customer_request("fuel"),
                    class_name="op-card",
                    width="100%",
                    height="90px",
                    border_radius="16px",
                    cursor="pointer",
                    align="center",
                    justify="center",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            # Request Status Overlay
            rx.cond(
                OperationalState.request_status == "searching",
                rx.vstack(
                    rx.text("Buscando o melhor profissional...", weight="bold", color=COLORS["text"], text_align="center"),
                    rx.spinner(size="1"),
                    spacing="3",
                    align="center",
                    padding="1.2rem",
                    width="100%",
                    background="rgba(255,255,255,0.9)",
                    border_radius="16px",
                    margin_top="1rem",
                    border=f"1px solid {COLORS['line']}",
                ),
            ),
            rx.cond(
                OperationalState.request_status == "matched",
                rx.vstack(
                    rx.text("✅ Profissional encontrado!", weight="bold", color=COLORS["emergency_orange"], text_align="center"),
                    rx.text(
                        f"Preço estimado: {OperationalState.request_price_text} · Distância: {OperationalState.request_distance_text}",
                        font_size="0.9rem",
                        color=COLORS["text"],
                        text_align="center",
                    ),
                    rx.button("Cancelar Pedido", on_click=OperationalState.set_request_status("idle"), class_name="secondary-button", size="1"),
                    spacing="3",
                    align="center",
                    padding="1.2rem",
                    width="100%",
                    background="rgba(255,255,255,0.9)",
                    border_radius="16px",
                    margin_top="1rem",
                    border=f"1px solid {COLORS['line']}",
                ),
            ),
            rx.cond(
                OperationalState.request_error_message != "",
                rx.vstack(
                    rx.text(OperationalState.request_error_message, class_name="error-message", text_align="center"),
                    rx.cond(
                        OperationalState.show_profile_link,
                        rx.button(
                            "Ir para o perfil",
                            on_click=OperationalState.open_profile_for_request,
                            class_name="secondary-button",
                        ),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
            ),
            rx.cond(
                OperationalState.request_id != None,
                rx.button(
                    rx.hstack(rx.text("💬"), rx.text("Mensagens do chamado"), spacing="2"),
                    on_click=[
                        OperationalState.open_client_message_panel,
                        OperationalState.poll_service_messages,
                    ],
                    class_name="secondary-button",
                    width="100%",
                ),
            ),
            width="100%",
            padding="1rem",
            background="rgba(255,255,255,0.8)",
            backdrop_filter="blur(15px)",
            border_radius="2rem 2rem 0 0",
            position="absolute",
            bottom="0",
            left="0",
            right="0",
            z_index="100",
            border="1px solid rgba(255,255,255,0.5)",
            box_shadow="0 -10px 30px rgba(0,0,0,0.1)",
            pointer_events="auto",
        ),
        client_message_panel(),
        rx.box(
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="10",
            pointer_events="none",
        ),
        rx.input(
            value=OperationalState.lat_lng_update_value,
            on_change=OperationalState.handle_lat_lng_update,
            id="lat-lng-trigger",
            display="none",
        ),
        width="100%",
        height="100vh",
        position="relative",
        overflow="hidden",
        # Geolocation Trigger
        on_mount=[
            rx.call_script(
                "navigator.geolocation.getCurrentPosition((pos) => { "
                "const { latitude: lat, longitude: lng } = pos.coords; "
                "window.updateUserMarker('customer-map', lat, lng); "
                "window.triggerReflexUpdate({ role: 'client', lat: lat, lng: lng }); "
                "});"
            ),
        ],
    )


def provider_dashboard() -> rx.Component:
    return rx.box(
        # Map Container
        rx.box(
            id="provider-map",
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="0",
            on_mount=[
                rx.call_script("window.initSOSMap('provider-map', [-23.5505, -46.6333], 13);"),
                OperationalState.poll_pending_requests,
            ],
        ),
        # Top Navigation Bar
        rx.hstack(
            rx.button(
                rx.text("🏠 Home"),
                on_click=rx.redirect("/home"),
                class_name="glass-panel",
                padding="0.5rem 1rem",
                border_radius="12px",
                font_size="0.8rem",
                weight="bold",
                cursor="pointer",
            ),
            rx.spacer(),
            rx.hstack(
                profile_avatar(),
                rx.text(
                    rx.cond(OperationalState.is_available, "SOU ONLINE", "SOU OFFLINE"),
                    font_size="0.8rem",
                    weight="bold",
                    color=COLORS["text"],
                ),
                rx.checkbox(
                    on_change=OperationalState.toggle_provider_status,
                    checked=OperationalState.is_available,
                ),
                spacing="3",
                align="center",
                class_name="glass-panel",
                padding="0.5rem 1rem",
                background="white",
                backdrop_filter="blur(10px)",
                box_shadow="0 2px 10px rgba(0,0,0,0.1)",
            ),
            position="absolute",
            top="2rem",
            left="2rem",
            right="2rem",
            z_index="100",
            pointer_events="auto",
            align="center",
        ),
        # Center Map Button
        rx.button(
            "🎯",
            on_click=rx.call_script("window.centerMap('provider-map')"),
            class_name="glass-panel",
            position="absolute",
            bottom="15rem",
            right="1rem",
            z_index="100",
            width="3rem",
            height="3rem",
            border_radius="50%",
            pointer_events="auto",
            cursor="pointer",
            font_size="1.5rem",
        ),
        # Active Calls List (Bottom)
        rx.vstack(
            rx.text("Chamados Disponíveis", weight="bold", size="5", color=COLORS["text"]),
            rx.vstack(
                rx.foreach(
                    OperationalState.active_calls,
                    lambda call: rx.hstack(
                        rx.vstack(
                            rx.text(call["service_type"], weight="bold", color=COLORS["text"]),
                            rx.text(f"ID: {call['id']}", font_size="0.7rem", color=COLORS["muted"]),
                            align="start",
                            spacing="1",
                        ),
                        rx.button(
                            "Aceitar",
                            on_click=OperationalState.accept_call(call["id"]),
                            class_name="primary-button",
                            size="1",
                        ),
                        justify="between",
                        width="100%",
                        padding="1rem",
                        class_name="op-card",
                        border_radius="12px",
                    )
                ),
                width="100%",
                spacing="2",
            ),
            rx.button(
                "Simular Novo Chamado",
                on_click=OperationalState.simulate_new_call,
                class_name="secondary-button",
                size="1",
                margin_top="1rem",
                width="100%",
            ),
            width="100%",
            padding="1.5rem",
            background="rgba(255,255,255,0.8)",
            backdrop_filter="blur(15px)",
            border_radius="2rem 2rem 0 0",
            position="absolute",
            bottom="0",
            left="0",
            right="0",
            z_index="100",
            border="1px solid rgba(255,255,255,0.5)",
            box_shadow="0 -10px 30px rgba(0,0,0,0.1)",
            pointer_events="auto",
        ),
        # Tracking Trigger
        rx.box(
            on_mount=rx.call_script(
                f"window.startSOSTracking({OperationalState.current_provider_id}, (lat, lng) => {{ "
                f"window.updateUserMarker('provider-map', lat, lng); "
                f"window.triggerReflexUpdate({{ role: 'provider', provider_id: {OperationalState.current_provider_id}, lat: lat, lng: lng }}); "
                f"}})"
            ),
            display="none",
        ),
        rx.input(
            value=OperationalState.lat_lng_update_value,
            on_change=OperationalState.handle_lat_lng_update,
            id="lat-lng-trigger",
            display="none",
        ),
        width="100%",
        height="100vh",
        position="relative",
        overflow="hidden",
    )


def profile_screen() -> rx.Component:
    """Shared authenticated profile screen for clients and providers."""
    return rx.center(
        rx.vstack(
            # Top Navigation / Back Button
            rx.hstack(
                rx.button(
                    rx.hstack(rx.text("←", font_size="1.2rem"), rx.text("Voltar")),
                    on_click=rx.cond(
                        AppState.user_role == "prestador",
                        rx.redirect("/home_provider"),
                        rx.redirect("/home_client"),
                    ),
                    class_name="secondary-button",
                    size="1",
                ),
                justify="start",
                width="100%",
                margin_bottom="2rem",
            ),
            # Header Section
            rx.vstack(
                rx.text(
                    rx.cond(AppState.user_role == "prestador", "perfil do prestador", "perfil do cliente"),
                    class_name="section-kicker",
                ),
                rx.heading("Mantenha seus dados em dia.", class_name="section-title", size="8"),
                rx.text("Mantenha seus dados atualizados para melhor assistência.", class_name="section-intro"),
                align="start",
                spacing="2",
                width="100%",
            ),
            # Main Content Area
            rx.vstack(
                # Profile Header with Avatar and Upload
                rx.vstack(
                    rx.upload(
                        rx.vstack(
                            rx.box(
                                rx.cond(
                                    AppState.profile_photo_preview != "",
                                    rx.image(
                                        src=AppState.profile_photo_preview,
                                        width="100%",
                                        height="100%",
                                        border_radius="50%",
                                        object_fit="cover",
                                    ),
                                    rx.center(
                                        rx.text(AppState.user_initials, font_size="2rem", weight="bold", color=COLORS["text"]),
                                        width="100%",
                                        height="100%",
                                        background=COLORS["line"],
                                        border_radius="50%",
                                    ),
                                ),
                                width="100px",
                                height="100px",
                                border=f"3px solid {COLORS['emergency_orange']}",
                                border_radius="50%",
                                overflow="hidden",
                                cursor="pointer",
                            ),
                            rx.text("Alterar Foto", font_size="0.8rem", weight="bold", color=COLORS["navy"]),
                            align="center",
                            spacing="2",
                        ),
                        on_drop=AppState.handle_profile_upload,
                        accept={"image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"]},
                        max_files=1,
                        multiple=False,
                        no_drag=False,
                        no_click=False,
                        class_name="profile-upload-dropzone",
                    ),
                    align="center",
                    spacing="3",
                    margin_bottom="2rem",
                ),
                # Basic Info
                rx.vstack(
                    rx.text("Informações Básicas", weight="bold", size="4", color=COLORS["navy"]),
                    rx.vstack(
                        rx.text("Nome", class_name="field-label"),
                        rx.input(
                            value=AppState.user_full_name,
                            on_change=AppState.set_user_full_name,
                            class_name="profile-input",
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                        ),
                        width="100%",
                        spacing="2",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("CPF", class_name="field-label"),
                        rx.input(
                            value=AppState.user_cpf,
                            on_change=AppState.set_user_cpf,
                            placeholder="000.000.000-00",
                            class_name="profile-input",
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                            background="#F1F5F9",
                            color=COLORS["text"],
                        ),
                        width="100%",
                        spacing="2",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Email", class_name="field-label"),
                        rx.input(
                            value=AppState.user_email,
                            on_change=AppState.set_user_email,
                            class_name="profile-input",
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                        ),
                        width="100%",
                        spacing="2",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Telefone", class_name="field-label"),
                        rx.input(
                            value=AppState.user_phone,
                            on_change=AppState.set_user_phone,
                            class_name="profile-input",
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                        ),
                        width="100%",
                        spacing="2",
                        align="start",
                    ),
                    spacing="3",
                    class_name="op-card",
                    width="100%",
                    align="start",
                ),
                # Role Specific: Provider Specialties
                rx.cond(
                    AppState.user_role == "prestador",
                    rx.vstack(
                        rx.text("Minhas Especialidades", weight="bold", size="4", color=COLORS["navy"]),
                        rx.grid(
                            rx.foreach(
                                [("tire", "Troca de Pneu"), ("battery", "Carga de Bateria"), ("mechanical", "Mecânica Geral"), ("fuel", "Combustível")],
                                lambda spec: rx.checkbox(
                                    rx.text(spec[1]),
                                    checked=OperationalState.current_provider_specialties.contains(spec[0]),
                                    on_change=lambda _: OperationalState.toggle_specialty(spec[0]),
                                    padding="0.5rem",
                                ),
                            ),
                            columns="2",
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        class_name="op-card",
                        width="100%",
                        align="start",
                    ),
                ),
                # Vehicles Section
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Meus Veículos", weight="bold", size="4", color=COLORS["navy"]),
                            rx.text("Seus veículos cadastrados", font_size="0.8rem", color=COLORS["text"]),
                            align="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            "Adicionar",
                            on_click=OperationalState.open_new_vehicle_modal,
                            class_name="secondary-button",
                            size="1",
                        ),
                        width="100%",
                        align="center",
                        justify="center",
                        margin_bottom="1rem",
                    ),
                    rx.vstack(
                        rx.foreach(
                            OperationalState.user_vehicles,
                            lambda v: vehicle_card(v),
                        ),
                        width="100%",
                        spacing="3",
                        align="start",
                    ),
                    spacing="3",
                    class_name="op-card",
                    width="100%",
                    align="start",
                ),
                rx.button(
                    rx.cond(AppState.profile_is_loading, "Salvando...", "Salvar/Atualizar Dados"),
                    on_click=AppState.save_profile,
                    disabled=AppState.profile_is_loading,
                    class_name="primary-button",
                    width="100%",
                ),
                rx.cond(
                    AppState.profile_error != "",
                    rx.text(AppState.profile_error, class_name="error-message"),
                ),
                rx.cond(
                    AppState.profile_message != "",
                    rx.text(AppState.profile_message, class_name="success-message"),
                ),
                width="100%",
                max_width="600px",
                spacing="5",
                align="start",
            ),
            align="start",
            spacing="6",
            padding="2rem 1rem",
            width="100%",
            max_width="600px",
        ),
        rx.cond(
            OperationalState.show_vehicle_modal,
            vehicle_modal(),
        ),
        on_mount=[AuthState.load_profile, OperationalState.load_user_vehicles],
        background=COLORS["background"],
        width="100%",
        min_height="100vh",
    )



def map_test_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Teste de Mapa Leaflet", size="7"),
            rx.box(
                rx.html(
                    '<div id="map" style="height: 400px; width: 100%; border-radius: 16px; border: 1px solid #E2E8F0;"></div>'
                    '<script>'
                    'var map = L.map("map").setView([-23.5505, -46.6333], 13);'
                    'L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {'
                    'attribution: "&copy; OpenStreetMap contributors"}).addTo(map);'
                    'L.marker([-23.5505, -46.6333]).addTo(map).bindPopup("Você está aqui!").openPopup();'
                    '</script>'
                ),
                width="100%",
                max_width="800px",
            ),
            rx.button("Voltar", on_click=AppState.return_to_presentation, class_name="secondary-button"),
            spacing="4",
            align="center",
        ),
        padding="2rem",
    )


def home_screen() -> rx.Component:
    """Dynamic home screen that redirects based on user role."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Carregando seu painel...", weight="bold"),
            align="center",
            spacing="4",
        ),
        on_mount=rx.cond(
            AppState.user_role == "prestador",
            rx.redirect("/home_provider"),
            rx.redirect("/home_client"),
        ),
    )

def index() -> rx.Component:
    return rx.box(landing_page(), class_name="app-shell")


def shortcut_card(icon: str, label: str, action) -> rx.Component:
    """Render one quick-access card for the client home."""
    return rx.box(
        rx.vstack(
            rx.text(icon, font_size="1.8rem"),
            rx.text(label, weight="bold", color=COLORS["navy"], text_align="center"),
            align="center",
            spacing="2",
        ),
        class_name="op-card",
        width="100%",
        aspect_ratio="1",
        cursor="pointer",
        on_click=action,
    )


def user_home_screen() -> rx.Component:
    """Repaginated home screen for the client focusing on hierarchy and contrast."""
    return rx.hstack(
        # LEFT SIDE: CONTROL PANEL
        rx.vstack(
            # 1. Header Section
            rx.hstack(
                rx.vstack(
                    rx.text("Olá,", font_size="1rem", color=COLORS["muted"]),
                    rx.text(AppState.user_full_name, weight="bold", font_size="1.4rem", color=COLORS["navy"]),
                    rx.text("Cliente / Motorista", color=COLORS["muted"], font_size=".85rem"),
                    align="start",
                    spacing="0",
                ),
                rx.spacer(),
                rx.box(
                    profile_avatar(),
                    border=f"2px solid {COLORS['line']}",
                    border_radius="50%",
                    padding="2px",
                    box_shadow="0 2px 8px rgba(0,0,0,0.1)",
                    cursor="pointer",
                    on_click=rx.redirect("/profile"),
                ),
                width="100%",
                justify="between",
                align="center",
                margin_bottom="2rem",
            ),
            # 2. Hero Section (Request Help)
            rx.cond(
                AppState.active_call_status == None,
                # State A: No active call
                rx.button(
                    rx.vstack(
                        rx.text("🚨", font_size="3.5rem"),
                        rx.text("Solicitar Socorro", color="white", weight="bold", font_weight="bold", font_size="1.6rem"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=rx.redirect("/customer"),
                    class_name="primary-button sos-request-button",
                    width="100%",
                    height="14rem",
                    border_radius="32px",
                    color="white",
                    cursor="pointer",
                ),
                # State B: Active call
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text("🕒", font_size="1.5rem"),
                            rx.text("Chamado em andamento", weight="bold", size="5", color=COLORS["navy"]),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(f"Chegada estimada: {AppState.active_call_eta}", color=COLORS["muted"], font_size="1rem"),
                        rx.button(
                            "Acompanhar Agora",
                            on_click=rx.redirect("/customer"),
                            class_name="primary-button",
                            width="100%",
                            margin_top="1rem",
                        ),
                        align="start",
                        spacing="3",
                    ),
                    padding="1.5rem",
                    background="white",
                    border=f"2px solid {COLORS['emergency_orange']}",
                    border_radius="24px",
                    width="100%",
                    box_shadow="0 4px 12px rgba(249,115,22,0.15)",
                ),
            ),
            # 3. Shortcuts Grid
            rx.grid(
                shortcut_card("🚗", "Meus Veículos", rx.redirect("/profile")),
                shortcut_card("📜", "Histórico", rx.redirect("/profile")),
                shortcut_card("⚙️", "Perfil", rx.redirect("/profile")),
                columns="3",
                spacing="4",
                width="100%",
                margin_top="2rem",
            ),
            # 4. Bottom Section (Location Context - status text only)
            rx.vstack(
                rx.hstack(
                    rx.text("📍 Localização Atual", weight="bold", font_size="0.9rem", color=COLORS["navy"]),
                    rx.spacer(),
                    rx.text("✅ Nenhum chamado ativo", font_size="0.75rem", color="#22C55E", weight="bold"),
                    width="100%",
                    margin_bottom="1rem",
                    align="center",
                ),
                align="start",
                width="100%",
                margin_top="3rem",
            ),
            align="start",
            spacing="6",
            width=["100%", "100%", "100%", "420px"],
            flex=["none", "none", "none", "0 0 420px"],
            height=["auto", "auto", "auto", "100%"],
            padding="2rem",
            background="white",
            border_radius=["24px 24px 0 0", "24px 24px 0 0", "24px 24px 0 0", "24px"],
        ),
        # RIGHT SIDE: MAP AREA
        rx.box(
            rx.box(
                id="user-home-map-fixed",
                width="100%",
                height="100%",
                on_mount=rx.call_script(
                    "window.initSOSMap('user-home-map-fixed', [-23.5505, -46.6333], 13);"
                ),
            ),
            width=["100%", "100%", "100%", "auto"],
            height=["60vh", "60vh", "60vh", "100%"],
            flex=["none", "none", "none", "1"],
            border_radius=["24px", "24px", "24px", "24px"],
            overflow="hidden",
        ),
        width="100vw",
        height="100vh",
        display="flex",
        flex_direction=["column", "column", "column", "row"],
        align="stretch",
        spacing="0",
        padding="0",
        overflow_y=["auto", "auto", "auto", "hidden"],
        class_name="user-home-root",
    )

def provider_home_screen() -> rx.Component:
    """Central hub for the provider."""
    return rx.box(
        # Header
        rx.hstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Área do prestador", weight="bold", color=COLORS["navy"]),
                    rx.text(
                        "Receba chamados quando estiver disponível",
                        font_size="0.75rem",
                        color=COLORS["muted"],
                    ),
                    align="start",
                    spacing="1",
                ),
                rx.button(
                    rx.hstack(
                        rx.box(
                            width="0.65rem",
                            height="0.65rem",
                            border_radius="50%",
                            background=rx.cond(OperationalState.is_available, "#16A34A", "#64748B"),
                        ),
                        rx.text(
                            rx.cond(OperationalState.is_available, "Disponível", "Indisponível"),
                            weight="bold",
                            color=rx.cond(OperationalState.is_available, "#166534", "#475569"),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    on_click=OperationalState.toggle_provider_status,
                    aria_label=rx.cond(
                        OperationalState.is_available,
                        "Disponível para chamados. Ative para ficar indisponível.",
                        "Indisponível para chamados. Ative para ficar disponível.",
                    ),
                    background=rx.cond(OperationalState.is_available, "#F0FDF4", "#F1F5F9"),
                    border=rx.cond(OperationalState.is_available, "1px solid #86EFAC", "1px solid #CBD5E1"),
                    border_radius="999px",
                    padding="0.65rem 0.9rem",
                    cursor="pointer",
                    flex_shrink="0",
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            profile_avatar(),
            position="fixed",
            top=["0.75rem", "1rem", "1.25rem"],
            left=["0.75rem", "1rem", "1.5rem"],
            right=["0.75rem", "1rem", "1.5rem"],
            z_index="3000",
            align="center",
            padding="0.75rem 1rem",
            background="rgba(255, 255, 255, 0.96)",
            border=f"1px solid {COLORS['line']}",
            border_radius="16px",
            box_shadow="0 4px 18px rgba(15,23,42,0.12)",
        ),
        # Main Body (50/50 Split)
        rx.vstack(
            # Upper Half: Map
            rx.box(
                rx.box(
                    id="provider-home-map",
                    position="absolute",
                    top="0",
                    right="0",
                    bottom="0",
                    left="0",
                    on_mount=[
                        rx.call_script(
                            "window.initSOSMap('provider-home-map', [-23.5505, -46.6333], 13);"
                        ),
                        rx.call_script(
                            "window.requestProviderMapLocation('provider-home-map');"
                        ),
                    ],
                ),
                rx.button(
                    rx.hstack(rx.text("◎", font_size="1.25rem"), rx.text("Centralizar no meu local", size="2"), spacing="2", align="center"),
                    on_click=rx.call_script(
                        "window.requestProviderMapLocation('provider-home-map');"
                    ),
                    aria_label="Centralizar o mapa na minha localização atual",
                    position="fixed",
                    top=["7rem", "7rem", "7rem"],
                    right=["0.75rem", "1rem", "1.5rem"],
                    z_index="2000",
                    background="white",
                    color=COLORS["navy"],
                    border=f"1px solid {COLORS['line']}",
                    border_radius="999px",
                    padding="0.65rem 0.9rem",
                    box_shadow="0 3px 12px rgba(15,23,42,0.18)",
                    cursor="pointer",
                ),
                rx.text(
                    "",
                    id="provider-location-status",
                    role="status",
                    aria_live="polite",
                    display="none",
                    position="absolute",
                    left=["0.75rem", "1rem", "1.5rem"],
                    bottom="1rem",
                    z_index="500",
                    max_width="min(80%, 28rem)",
                    padding="0.5rem 0.75rem",
                    background="rgba(255,255,255,0.96)",
                    color=COLORS["text"],
                    border_radius="10px",
                    box_shadow="0 2px 10px rgba(15,23,42,0.14)",
                    font_size="0.8rem",
                ),
                width="100%",
                height="50vh",
                position="relative",
                overflow="hidden",
            ),
            # Lower Half: Requests List
            rx.box(
                rx.cond(
                    OperationalState.is_available,
                    rx.vstack(
                        rx.text(
                            "Solicitações Próximas",
                            weight="bold",
                            size="5",
                            color=COLORS["navy"],
                            margin_bottom="1rem",
                        ),
                        rx.vstack(
                            rx.foreach(
                                OperationalState.available_requests,
                                lambda r: rx.hstack(
                                    rx.box(
                                        rx.text(r["service_icon"], font_size="1.8rem"),
                                        width="3rem",
                                        height="3rem",
                                        display="flex",
                                        align_items="center",
                                        justify_content="center",
                                        background="#FFF7ED",
                                        border_radius="12px",
                                        flex_shrink="0",
                                    ),
                                    rx.vstack(
                                        rx.text(r["type"], weight="bold", color=COLORS["navy"]),
                                        rx.text(f"👤 {r['user']} • 📍 {r['distance']}", font_size="0.8rem", color=COLORS["text"]),
                                        align="start",
                                        spacing="1",
                                    ),
                                    rx.spacer(),
                                    rx.hstack(
                                        rx.button("Aceitar", on_click=lambda: OperationalState.accept_request(r["id"]), class_name="primary-button", size="1"),
                                        rx.button("Recusar", on_click=lambda: OperationalState.refuse_request(r["id"]), class_name="secondary-button", size="1"),
                                        spacing="2",
                                    ),
                                    width="100%",
                                    padding="1rem",
                                    background="white",
                                    border=f"1px solid {COLORS['line']}",
                                    border_radius="12px",
                                    box_shadow="0 4px 12px rgba(15,23,42,0.08)",
                                    spacing="3",
                                ),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    rx.center(
                        rx.text("Você está indisponível para novos chamados", weight="bold", color=COLORS["muted"]),
                        width="100%",
                        height="100%",
                    ),
                ),
                width="100%",
                height="50vh",
                overflow_y="auto",
                padding="1rem",
                background="white",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        on_mount=[
            OperationalState.reset_provider_home,
            OperationalState.poll_pending_requests,
        ],
        background="white",
        width="100%",
        min_height="100vh",
    )


def service_details_screen() -> rx.Component:
    """Show the selected request details and route preview for a provider."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.button(
                    "← Voltar",
                    on_click=rx.redirect("/home_provider"),
                    class_name="secondary-button",
                    size="1",
                ),
                rx.heading("Detalhes do Atendimento", size="6", color=COLORS["navy"]),
                align="center",
                spacing="4",
                width="100%",
            ),
            rx.grid(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.text(
                                OperationalState.selected_request["service_icon"],
                                font_size="2rem",
                                color=COLORS["emergency_orange"],
                            ),
                            width="4rem",
                            height="4rem",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            background="#FFF7ED",
                            border_radius="16px",
                        ),
                        rx.vstack(
                            rx.text(OperationalState.selected_request["type"], weight="bold", size="5", color=COLORS["navy"]),
                            rx.text("Solicitação de atendimento", color=COLORS["muted"]),
                            align="start",
                            spacing="1",
                        ),
                        align="center",
                        spacing="4",
                    ),
                    rx.vstack(
                        rx.text("Cliente", class_name="field-label"),
                        rx.text(OperationalState.selected_request["user"], size="5", weight="bold", color=COLORS["navy"]),
                        rx.text(OperationalState.selected_request["address"], color=COLORS["text"]),
                        rx.text(f"Distância: {OperationalState.selected_request['distance']}", color=COLORS["muted"]),
                        align="start",
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.link(
                        rx.hstack(
                            rx.text("☎"),
                            rx.text("Ligar"),
                            width="100%",
                            justify="center",
                            align="center",
                            spacing="2",
                        ),
                        href=rx.cond(
                            OperationalState.selected_request["phone"] != "",
                            f"tel:{OperationalState.selected_request['phone']}",
                            "#",
                        ),
                        class_name="primary-button action-button",
                        width="auto",
                        padding_x="1.25rem",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.text("💬"),
                            rx.text("Mensagem"),
                            width="100%",
                            justify="center",
                            align="center",
                            spacing="2",
                        ),
                        class_name="secondary-button action-button",
                        width="auto",
                        padding_x="1.25rem",
                    ),
                    spacing="3",
                    width="100%",
                    ),
                    rx.vstack(
                        rx.text("Status do atendimento", class_name="field-label"),
                        rx.text("A caminho", color=COLORS["emergency_orange"], weight="bold"),
                        rx.hstack(
                            rx.button(
                                rx.hstack(rx.text("📍"), rx.text("Cheguei"), width="100%", justify="center", spacing="2"),
                                class_name="secondary-button action-button",
                                size="1",
                                width="auto",
                                padding_x="1rem",
                            ),
                            rx.button(
                                rx.hstack(rx.text("✓"), rx.text("Concluído"), width="100%", justify="center", spacing="2"),
                                class_name="secondary-button action-button",
                                size="1",
                                width="auto",
                                padding_x="1rem",
                            ),
                            spacing="3",
                        ),
                        align="start",
                        spacing="2",
                    ),
                    rx.link(
                        rx.hstack(
                            rx.text("➤"),
                            rx.text("Como Chegar"),
                            width="100%",
                            justify="center",
                            align="center",
                            spacing="2",
                        ),
                        href=OperationalState.selected_request["maps_url"],
                        is_external=True,
                        class_name="primary-button action-button",
                        width="auto",
                        padding_x="1.5rem",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.text("←"),
                            rx.text("Cancelar / Voltar"),
                            width="100%",
                            justify="center",
                            align="center",
                            spacing="2",
                        ),
                        on_click=rx.redirect("/home_provider"),
                        class_name="secondary-button action-button",
                        width="auto",
                        padding_x="1.5rem",
                    ),
                    class_name="op-card",
                    align="start",
                    spacing="5",
                    width="100%",
                ),
                rx.box(
                    rx.box(
                        id="service-details-map",
                        width="100%",
                        height="100%",
                        on_mount=rx.call_script(
                            "window.initSOSMap('service-details-map', [-23.5614, -46.6559], 14);"
                        ),
                    ),
                    width="100%",
                    height=["50vh", "50vh", "70vh"],
                    border_radius="20px",
                    overflow="hidden",
                ),
                columns="1",
                class_name="service-details-grid",
                spacing="6",
                width="100%",
            ),
            width="100%",
            max_width="1200px",
            padding=["1rem", "2rem", "3rem"],
            spacing="6",
        ),
        width="100%",
        min_height="100vh",
        background=COLORS["background"],
    )


def provider_service_progress_screen() -> rx.Component:
    """Full-screen attendance view after provider accepts a request."""
    return rx.box(
        rx.box(
            id="provider-service-progress-map",
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="0",
            on_mount=rx.call_script(OperationalState.atendimento_route_script),
        ),
        rx.hstack(
            rx.button(
                "← Home",
                on_click=rx.redirect("/home_provider"),
                class_name="secondary-button",
                size="1",
            ),
            rx.spacer(),
            profile_avatar(),
            position="absolute",
            top="1rem",
            left="1rem",
            right="1rem",
            z_index="100",
            align="center",
        ),
        # Top Progress Pill (The Yellow Line/Pill)
        rx.box(
            rx.hstack(
                rx.text("🕒", font_size="1.2rem"),
                rx.vstack(
                    rx.text(
                        OperationalState.atendimento_status_text,
                        font_size="0.8rem",
                        font_weight="bold",
                        color=COLORS["emergency_orange"],
                        letter_spacing="0.08em",
                        text_transform="uppercase",
                    ),
                    rx.text(
                        rx.cond(
                            OperationalState.atendimento_mock,
                            OperationalState.atendimento_mock["tipo_problema"],
                            "Atendimento",
                        ),
                        font_size="1rem",
                        font_weight="bold",
                        color=COLORS["navy"],
                    ),
                    align="start",
                    spacing="0",
                ),
                spacing="3",
                align="center",
            ),
            class_name="glass-panel",
            border_radius="14px",
            padding="0.7rem 1.2rem",
            position="absolute",
            top="5rem",
            left="50%",
            transform="translateX(-50%)",
            z_index="110",
            width="auto",
            background="white",
            border=f"2px solid {COLORS['emergency_orange']}",
            box_shadow="0 4px 12px rgba(0,0,0,0.1)",
        ),
        # Bottom Summary Panel
        rx.vstack(
            rx.box(
                rx.vstack(
                    # User Header
                    rx.hstack(
                        rx.box(
                            rx.text(
                                rx.cond(
                                    OperationalState.atendimento_mock,
                                    OperationalState.atendimento_mock["service_icon"],
                                    "🛠️",
                                ),
                                font_size="1.5rem",
                            ),
                            width="3rem",
                            height="3rem",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            background="#FFF7ED",
                            border_radius="12px",
                        ),
                        rx.vstack(
                            rx.text(
                                rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["nome"], "Cliente"),
                                font_size="1.1rem",
                                font_weight="bold",
                                color=COLORS["navy"],
                            ),
                            rx.text(
                                rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["tipo_problema"], "Solicitação"),
                                font_size="0.9rem",
                                color=COLORS["text"],
                            ),
                            align="start",
                            spacing="0",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    # Detailed Summary Grid
                    rx.grid(
                        rx.vstack(
                            rx.text("Veículo", class_name="field-label"),
                            rx.text(
                                rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["veiculo"], "Não informado"),
                                color=COLORS["text"],
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Endereço", class_name="field-label"),
                            rx.text(
                                rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["endereco"], "Não informado"),
                                color=COLORS["text"],
                            ),
                            spacing="1",
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Observação", class_name="field-label"),
                        rx.text(
                            rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["observacao"], "Sem observações."),
                            color=COLORS["muted"],
                            font_size="0.85rem",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    # Action Buttons
                    rx.hstack(
                        # Button to notify arrival (Sends message/updates status)
                        rx.button(
                            rx.hstack(rx.text("💬"), rx.text("Avisar Chegada"), spacing="2"),
                            on_click=OperationalState.notify_arrival,
                            class_name="secondary-button",
                            size="2",
                            padding_x="1rem",
                        ),
                        rx.button(
                            rx.hstack(rx.text("💬"), rx.text("Mensagens"), spacing="2"),
                            on_click=[
                                OperationalState.open_message_panel,
                                OperationalState.poll_service_messages,
                            ],
                            class_name="secondary-button",
                            size="2",
                            padding_x="1rem",
                        ),
                        # Button to open map in external app
                        rx.button(
                            rx.hstack(rx.text("📍"), rx.text("Abrir GPS"), spacing="2"),
                            on_click=rx.redirect(OperationalState.atendimento_mock["maps_url"]),
                            class_name="primary-button",
                            size="2",
                            padding_x="1rem",
                        ),
                        width="100%",
                        justify="between",
                        spacing="3",
                    ),
                    # Phase Advancement Button
                    rx.button(
                        OperationalState.atendimento_next_action_label,
                        on_click=OperationalState.advance_atendimento_phase,
                        class_name="primary-button",
                        width="100%",
                        margin_top="1rem",
                        size="3",
                        font_weight="bold",
                    ),
                    spacing="5",
                    width="100%",
                ),
                class_name="op-card",
                width="100%",
                max_width="42rem",
                background="white",
                border_radius="24px",
                padding="1.5rem",
                box_shadow="0 10px 30px rgba(0,0,0,0.15)",
            ),
            width="100%",
            align="center",
            position="absolute",
            left="0",
            right="0",
            bottom="1.5rem",
            z_index="120",
            padding_x="1rem",
        ),
        service_message_panel(),
        # Cancel Confirmation Modal
        rx.cond(
            OperationalState.show_cancel_confirm,
            rx.box(
                rx.box(
                    rx.vstack(
                        rx.heading("Cancelar atendimento", size="5", color=COLORS["navy"]),
                        rx.text("Tem certeza que quer cancelar?", color=COLORS["text"]),
                        rx.hstack(
                            rx.button(
                                "Voltar",
                                on_click=OperationalState.close_cancel_confirm,
                                class_name="secondary-button",
                                width="100%",
                            ),
                            rx.button(

                                "Sim, cancelar",
                                on_click=OperationalState.confirm_cancel_atendimento,
                                class_name="primary-button",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                        align="start",
                    ),
                    width="min(100%, 24rem)",
                    background="white",
                    border_radius="16px",
                    padding="1.2rem",
                    box_shadow="0 20px 50px rgba(0,0,0,0.25)",
                ),
                position="fixed",
                inset="0",
                z_index="130",
                display="flex",
                align_items="center",
                justify_content="center",
                background="rgba(2,6,23,0.5)",
                padding="1rem",
            ),
        ),
        width="100%",
        height="100vh",
        position="relative",
        overflow="hidden",
        background=COLORS["background"],
    )


def service_message_panel() -> rx.Component:
    """Render the conversation overlay for the active service request."""
    return rx.cond(
        OperationalState.show_message_panel,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Mensagens", size="5", color=COLORS["navy"]),
                        rx.spacer(),
                        rx.button(
                            "×",
                            on_click=OperationalState.close_message_panel,
                            class_name="secondary-button",
                            size="1",
                            aria_label="Fechar mensagens",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        OperationalState.message_sync_status,
                        role="status",
                        aria_live="polite",
                        font_size="0.75rem",
                        color=COLORS["muted"],
                    ),
                    rx.box(
                        rx.cond(
                            OperationalState.service_messages,
                            rx.vstack(
                                rx.foreach(
                                    OperationalState.service_messages,
                                    lambda message: rx.box(
                                        rx.text(message["message_text"], color=COLORS["text"]),
                                        rx.text(
                                            f"Remetente #{message['sender_id']}",
                                            color=COLORS["muted"],
                                            font_size="0.75rem",
                                        ),
                                        padding="0.75rem",
                                        border_radius="12px",
                                        background="#F8FAFC",
                                        width="100%",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.center(
                                rx.text("Nenhuma mensagem ainda.", color=COLORS["muted"]),
                                min_height="5rem",
                                width="100%",
                            ),
                        ),
                        max_height="14rem",
                        overflow_y="auto",
                        width="100%",
                        padding="0.25rem",
                    ),
                    rx.cond(
                        OperationalState.message_error != "",
                        rx.text(OperationalState.message_error, class_name="error-message"),
                        rx.text(" ", height="1.2rem"),
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Escreva uma mensagem...",
                            value=OperationalState.message_draft,
                            on_change=OperationalState.set_message_draft,
                            class_name="profile-input",
                            width="100%",
                        ),
                        rx.button(
                            "Enviar",
                            on_click=OperationalState.send_message,
                            class_name="primary-button",
                            size="2",
                        ),
                        width="100%",
                        align="center",
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                ),
                width="min(100%, 34rem)",
                background="white",
                border_radius="16px",
                padding="1.2rem",
                box_shadow="0 20px 50px rgba(0,0,0,0.25)",
            ),
            position="fixed",
            inset="0",
            z_index="140",
            display="flex",
            align_items="center",
            justify_content="center",
            background="rgba(2,6,23,0.5)",
            padding="1rem",
        ),
    )


def client_message_panel() -> rx.Component:
    """Render the client-side conversation overlay for the active request."""
    return rx.cond(
        OperationalState.show_client_message_panel,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Mensagens do chamado", size="5", color=COLORS["navy"]),
                        rx.spacer(),
                        rx.button(
                            "×",
                            on_click=OperationalState.close_client_message_panel,
                            class_name="secondary-button",
                            size="1",
                            aria_label="Fechar mensagens",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        OperationalState.message_sync_status,
                        role="status",
                        aria_live="polite",
                        font_size="0.75rem",
                        color=COLORS["muted"],
                    ),
                    rx.box(
                        rx.cond(
                            OperationalState.service_messages,
                            rx.vstack(
                                rx.foreach(
                                    OperationalState.service_messages,
                                    lambda message: rx.box(
                                        rx.text(message["message_text"], color=COLORS["text"]),
                                        rx.text(
                                            f"Remetente #{message['sender_id']}",
                                            color=COLORS["muted"],
                                            font_size="0.75rem",
                                        ),
                                        padding="0.75rem",
                                        border_radius="12px",
                                        background="#F8FAFC",
                                        width="100%",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.center(
                                rx.text("Nenhuma mensagem ainda.", color=COLORS["muted"]),
                                min_height="5rem",
                                width="100%",
                            ),
                        ),
                        max_height="14rem",
                        overflow_y="auto",
                        width="100%",
                        padding="0.25rem",
                    ),
                    rx.cond(
                        OperationalState.client_message_error != "",
                        rx.text(OperationalState.client_message_error, class_name="error-message"),
                        rx.text(" ", height="1.2rem"),
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Escreva uma mensagem...",
                            value=OperationalState.client_message_draft,
                            on_change=OperationalState.set_client_message_draft,
                            class_name="profile-input",
                            width="100%",
                        ),
                        rx.button(
                            "Enviar",
                            on_click=OperationalState.send_client_message,
                            class_name="primary-button",
                            size="2",
                        ),
                        width="100%",
                        align="center",
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                ),
                width="min(100%, 34rem)",
                background="white",
                border_radius="16px",
                padding="1.2rem",
                box_shadow="0 20px 50px rgba(0,0,0,0.25)",
            ),
            position="fixed",
            inset="0",
            z_index="140",
            display="flex",
            align_items="center",
            justify_content="center",
            background="rgba(2,6,23,0.5)",
            padding="1rem",
        ),
    )


def service_finalized_screen() -> rx.Component:
    """Simple finalization summary after completing attendance."""
    return rx.center(
        rx.vstack(
            rx.text("atendimento finalizado", class_name="section-kicker"),
            rx.heading("Chamado concluído com sucesso", class_name="section-title", size="7"),
            rx.text(
                "O atendimento foi encerrado e você já pode aceitar novos chamados.",
                class_name="section-intro",
                text_align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        rx.cond(
                            OperationalState.atendimento_mock,
                            f"Cliente: {OperationalState.atendimento_mock['nome']}",
                            "Cliente: -",
                        ),
                        color=COLORS["text"],
                    ),
                    rx.text(
                        rx.cond(
                            OperationalState.atendimento_mock,
                            f"Serviço: {OperationalState.atendimento_mock['tipo_problema']}",
                            "Serviço: -",
                        ),
                        color=COLORS["text"],
                    ),
                    rx.text(
                        rx.cond(
                            OperationalState.atendimento_mock,
                            f"Endereço: {OperationalState.atendimento_mock['endereco']}",
                            "Endereço: -",
                        ),
                        color=COLORS["muted"],
                    ),
                    align="start",
                    spacing="1",
                ),
                class_name="op-card",
                width="100%",
            ),
            rx.button(
                "Voltar para Home do Colaborador",
                on_click=OperationalState.finish_atendimento_and_back_home,
                class_name="primary-button",
                width="100%",
            ),
            spacing="5",
            width="min(100%, 38rem)",
            align="start",
            class_name="login-panel",
        ),
        min_height="100vh",
        padding="1rem",
        background=COLORS["background"],
    )


def protected_page(page: Callable[[], rx.Component]) -> rx.Component:
    """Restore and validate the session before rendering a protected page."""
    return rx.box(
        rx.cond(
            AuthState.session_validated,
            page(),
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Validando sua sessão...", weight="bold"),
                    align="center",
                    spacing="4",
                ),
                min_height="100vh",
            ),
        ),
        on_mount=AuthState.restore_session,
        width="100%",
        min_height="100vh",
    )


app = rx.App(
    style=GLOBAL_STYLE,
    head_components=[
        rx.el.link(
            rel="stylesheet",
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
        ),
        rx.script(
            src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            defer=True,
        ),
        rx.script('''
        (() => {
        let leafletWaitAttempts = 0;
        window.setProviderLocationMessage = function(message) {
            const status = document.getElementById("provider-location-status");
            if (status) {
                status.textContent = message;
                status.style.display = message ? "block" : "none";
            }
        };
        window.requestProviderMapLocation = function(mapId, attempts = 0) {
            if (window.locateProviderOnMap && window.sosMaps && window.sosMaps[mapId]) {
                window.locateProviderOnMap(mapId);
            } else if (attempts < 50) {
                window.setTimeout(() => window.requestProviderMapLocation(mapId, attempts + 1), 100);
            } else {
                window.setProviderLocationMessage("O mapa ainda está carregando. Tente novamente.");
            }
        };
        const initializeSOSMaps = () => {
            if (window.sosMapsInitialized) return;
            if (!window.L) {
                if (leafletWaitAttempts < 100) {
                    leafletWaitAttempts += 1;
                    window.setTimeout(initializeSOSMaps, 50);
                } else {
                    console.error("Leaflet did not load; map features are unavailable.");
                }
                return;
            }
            window.sosMapsInitialized = true;

        window.sosMaps = {};
        window.sosMarkers = {};
        window.sosUserMarkers = {};
        window.sosProviderLocationMarkers = {};

        window.initSOSMap = function(id, center, zoom) {
            if (window.sosMaps[id]) {
                return window.sosMaps[id];
            }
            const map = L.map(id, { zoomControl: false }).setView(center, zoom);
            L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "" }).addTo(map);
            window.sosMaps[id] = map;
            setTimeout(() => map.invalidateSize(), 200);
            return map;
        };

        window.updateUserMarker = function(mapId, lat, lng) {
            const map = window.sosMaps[mapId];
            if (!map) return;

            if (window.sosUserMarkers[mapId]) {
                window.sosUserMarkers[mapId].setLatLng([lat, lng]);
            } else {
                window.sosUserMarkers[mapId] = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: "user-marker",
                        html: "🔵",
                        iconSize: [20, 20]
                    })
                }).addTo(map).bindPopup("Você está aqui").openPopup();
            }
            map.setView([lat, lng], 13);
        };

        window.updateSOSMarkers = function(mapId, providers, isClient = false) {
            const map = window.sosMaps[mapId];
            if (!map) return;

            if (window.sosMarkers[mapId]) {
                window.sosMarkers[mapId].forEach(m => map.removeLayer(m));
            }
            window.sosMarkers[mapId] = [];

            providers.forEach(p => {
                const marker = L.marker([p.lat, p.lng], {
                    icon: L.divIcon({
                        className: isClient ? "user-marker" : "provider-marker",
                        html: isClient ? "🔵" : "🛠️"
                    })
                }).addTo(map).bindPopup(p.name);
                window.sosMarkers[mapId].push(marker);
            });
        };

        window.setSOSCenter = function(mapId, lat, lng) {
            const map = window.sosMaps[mapId];
            if (map) map.setView([lat, lng], 13);
        };

        window.centerMap = function(mapId) {
            const map = window.sosMaps[mapId];
            const userMarker = window.sosUserMarkers[mapId];
            if (map && userMarker) {
                map.setView(userMarker.getLatLng(), 13);
            }
        };

        window.locateProviderOnMap = function(mapId) {
            const map = window.sosMaps[mapId];
            if (!map) {
                window.setProviderLocationMessage("O mapa ainda está carregando. Tente novamente.");
                return;
            }
            if (!navigator.geolocation) {
                window.setProviderLocationMessage(
                    "Este navegador não oferece acesso à localização. O mapa permanece na posição padrão."
                );
                return;
            }

            window.setProviderLocationMessage("Localizando sua posição...");
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const location = [
                        position.coords.latitude,
                        position.coords.longitude
                    ];
                    let marker = window.sosProviderLocationMarkers[mapId];
                    if (!marker) {
                        marker = L.marker(location, {
                            icon: L.divIcon({
                                className: "provider-marker",
                                html: "🛠️",
                                iconSize: [28, 28],
                                iconAnchor: [14, 14]
                            })
                        }).addTo(map).bindPopup("Você está aqui");
                        window.sosProviderLocationMarkers[mapId] = marker;
                    } else {
                        marker.setLatLng(location);
                    }
                    map.setView(location, 14);
                    window.setProviderLocationMessage("");
                },
                (error) => {
                    const messages = {
                        1: "Permita o acesso à localização no navegador e tente novamente.",
                        2: "Não foi possível obter sua localização. Verifique o sinal e tente novamente.",
                        3: "A localização demorou para responder. Tente centralizar novamente."
                    };
                    window.setProviderLocationMessage(
                        messages[error.code] || "Não foi possível obter sua localização. Tente novamente."
                    );
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
            );
        };

        window.showSOSRoute = async function(mapId, startCoords, endCoords) {
            const map = window.sosMaps[mapId];
            if (!map) return;

            if (window.sosRouteLine && map.hasLayer(window.sosRouteLine)) {
                map.removeLayer(window.sosRouteLine);
            }

            const start = L.latLng(startCoords[0], startCoords[1]);
            const end = L.latLng(endCoords[0], endCoords[1]);

            L.marker(start, {
                icon: L.divIcon({ className: "provider-marker", html: "🛠️" })
            }).addTo(map).bindPopup("Você (colaborador)");

            L.marker(end, {
                icon: L.divIcon({ className: "user-marker", html: "🔵" })
            }).addTo(map).bindPopup("Usuário socorrido");

            try {
                // Fetch real road geometry from OSRM
                const url = `https://router.project-osrm.org/route/v1/driving/${startCoords[1]},${startCoords[0]};${endCoords[1]},${endCoords[0]}?overview=full&geometries=geojson`;
                const response = await fetch(url);
                const data = await response.json();

                if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
                    const coords = data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]);
                    window.sosRouteLine = L.polyline(coords, {
                        color: "#F97316",
                        weight: 5,
                        opacity: 0.85,
                    }).addTo(map);
                } else {
                    throw new Error("Route not found");
                }
            } catch (e) {
                console.error("Routing error, falling back to straight line:", e);
                window.sosRouteLine = L.polyline([start, end], {
                    color: "#F97316",
                    weight: 5,
                    opacity: 0.85,
                    dashArray: '5, 10'
                }).addTo(map);
            }

            map.fitBounds(window.sosRouteLine.getBounds(), { padding: [40, 40] });
        };

        window.triggerReflexUpdate = function(data) {
            const input = document.getElementById('lat-lng-trigger');
            if (!input) return;
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeInputValueSetter.call(input, JSON.stringify(data));
            const event = new Event('input', { bubbles: true });
            input.dispatchEvent(event);
        };

        window.startSOSTracking = function(providerId, onLocationUpdate) {
            if (!navigator.geolocation) return;
            navigator.geolocation.watchPosition(
                (pos) => onLocationUpdate(pos.coords.latitude, pos.coords.longitude),
                (err) => console.error("Geolocation error:", err),
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
            );
        };
        };

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", initializeSOSMaps, { once: true });
        } else {
            initializeSOSMaps();
        }
        })();
        '''),
    ],
)
app.add_page(index, route="/", title="SOS Drive | Assistência quando importa")
app.add_page(signup_screen, route="/signup", title="Cadastro | SOS Drive")
app.add_page(login_screen, route="/login", title="Login | SOS Drive")
app.add_page(lambda: protected_page(home_screen), route="/home", title="Home | SOS Drive")
app.add_page(lambda: protected_page(user_home_screen), route="/home_client", title="Home Cliente | SOS Drive")
app.add_page(lambda: protected_page(customer_dashboard), route="/customer", title="Dashboard Cliente | SOS Drive")
app.add_page(lambda: protected_page(provider_dashboard), route="/provider", title="Dashboard Prestador | SOS Drive")
app.add_page(lambda: protected_page(provider_home_screen), route="/home_provider", title="Solicitações Próximas | SOS Drive")
app.add_page(lambda: protected_page(service_details_screen), route="/service-details", title="Detalhes do Atendimento | SOS Drive")
app.add_page(lambda: protected_page(provider_service_progress_screen), route="/provider-service-progress", title="Atendimento em Andamento | SOS Drive")
app.add_page(lambda: protected_page(service_finalized_screen), route="/service-finalized", title="Chamado Finalizado | SOS Drive")
app.add_page(lambda: protected_page(profile_screen), route="/profile", title="Meu Perfil | SOS Drive")
app.add_page(lambda: protected_page(profile_screen), route="/perfil-cliente", title="Perfil Cliente | SOS Drive")
app.add_page(lambda: protected_page(profile_screen), route="/perfil-prestador", title="Perfil Prestador | SOS Drive")
app.add_page(lambda: protected_page(map_test_screen), route="/test-map", title="Teste de Mapa | SOS Drive")
