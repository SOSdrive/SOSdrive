"""SOS Drive Reflex application."""

from __future__ import annotations

import os
from pathlib import Path

import reflex as rx
import requests

from styles import GLOBAL_STYLE, COLORS


def validate_signup(name: str, email: str, password: str) -> str:
    """Return a local signup validation message, or an empty string."""
    if not all((name.strip(), email.strip(), password)):
        return "Preencha nome, email e senha para continuar."
    return ""


def login_with_xano(email: str, password: str, api_url: str) -> tuple[str, int]:
    """Authenticate a driver through Xano and return its token and user id."""
    normalized_url = api_url.strip().rstrip("/")
    if not normalized_url:
        raise RuntimeError("XANO_API_URL is not configured")

    response = requests.post(
        f"{normalized_url}/auth/login",
        json={"email": email.strip().lower(), "password": password},
        timeout=10,
    )
    if response.status_code in {401, 403}:
        raise PermissionError("Invalid credentials")
    response.raise_for_status()
    payload = response.json()
    auth_token = payload.get("authToken")
    user_id = payload.get("user_id")
    if not auth_token or not isinstance(user_id, int):
        raise ValueError("Unexpected login response")
    return auth_token, user_id


class AppState(rx.State):
    """Application state for navigation and driver authentication."""

    screen: str = "presentation"
    email: str = ""
    password: str = ""
    signup_name: str = ""
    signup_email: str = ""
    signup_password: str = ""
    signup_role: str = "client"
    auth_token: str = ""
    user_id: int | None = None
    error_message: str = ""
    signup_message: str = ""
    is_loading: bool = False

    def open_signup(self) -> None:
        self.screen = "signup"
        self.error_message = ""
        self.signup_message = ""

    def open_login(self) -> None:
        self.screen = "login"
        self.error_message = ""
        self.signup_message = ""

    def choose_signup_role(self, role: str) -> None:
        if role in {"client", "provider"}:
            self.signup_role = role

    def set_signup_name(self, value: str) -> None:
        self.signup_name = value

    def set_signup_email(self, value: str) -> None:
        self.signup_email = value

    def set_signup_password(self, value: str) -> None:
        self.signup_password = value

    def submit_signup(self) -> None:
        self.signup_message = ""
        self.error_message = ""
        self.error_message = validate_signup(self.signup_name, self.signup_email, self.signup_password)
        if self.error_message:
            self.signup_password = ""
            return
        self.signup_message = "Cadastro preparado. A conexão com o banco será adicionada na próxima etapa."
        self.signup_password = ""

    def set_email_value(self, value: str) -> None:
        self.email = value

    def set_password_value(self, value: str) -> None:
        self.password = value

    def return_to_presentation(self) -> None:
        self.screen = "presentation"
        self.error_message = ""
        self.signup_message = ""
        self.password = ""
        self.signup_password = ""

    def open_map_test(self) -> None:
        self.screen = "map_test"

    def logout(self) -> None:
        self.screen = "presentation"
        self.auth_token = ""
        self.user_id = None
        self.email = ""
        self.password = ""
        self.signup_name = ""
        self.signup_email = ""
        self.signup_password = ""
        self.error_message = ""
        self.signup_message = ""

    def get_xano_api_url(self) -> str:
        return os.getenv("XANO_API_URL", "").strip().rstrip("/")

    def login(self) -> None:
        """Authenticate through Xano without retaining the submitted password."""
        self.error_message = ""
        self.is_loading = True
        api_url = self.get_xano_api_url()
        if not api_url:
            self.error_message = "O login ainda não está configurado neste ambiente."
            self.password = ""
            self.is_loading = False
            return

        try:
            auth_token, user_id = login_with_xano(self.email, self.password, api_url)
            self.auth_token = auth_token
            self.user_id = user_id
            self.screen = "authenticated"
        except PermissionError:
            self.error_message = "Email ou senha inválidos."
        except (requests.RequestException, ValueError):
            self.error_message = "Não foi possível conectar ao serviço de login. Tente novamente."
        finally:
            self.password = ""
            self.is_loading = False

    def bypass_login_client(self) -> None:
        """Bypass login for testing as a client."""
        self.screen = "authenticated"

    def bypass_login_provider(self) -> None:
        """Bypass login for testing as a provider."""
        self.screen = "provider_dash"


class OperationalState(rx.State):
    """Operational state for map and service requests."""

    # Mock Data for Providers
    providers: list[dict] = [
        {"id": 1, "name": "João Socorro", "coords": [-23.5505, -46.6333], "specialties": ["tire", "battery"], "status": "online"},
        {"id": 2, "name": "Maria Assist", "coords": [-23.5550, -46.6350], "specialties": ["mechanical", "fuel"], "status": "online"},
        {"id": 3, "name": "SOS Rapidão", "coords": [-23.5450, -46.6300], "specialties": ["tire", "mechanical"], "status": "offline"},
        {"id": 4, "name": "Carlos Guincho", "coords": [-23.5600, -46.6400], "specialties": ["mechanical", "fuel"], "status": "online"},
    ]

    # Mock Data for Active Calls
    active_calls: list[dict] = [
        {"id": 101, "service_type": "Pneu Furado", "coords": [-23.5520, -46.6340], "status": "pending"},
        {"id": 102, "service_type": "Bateria", "coords": [-23.5580, -46.6310], "status": "pending"},
    ]

    # Customer Request state
    selected_service: str | None = None
    request_status: str = "idle" # idle, searching, matched

    # Provider identity (simulated)
    current_provider_id: int = 1
    current_provider_specialties: list[str] = ["tire", "battery"]

    def toggle_provider_status(self):
        """Toggle status of the current simulated provider."""
        for p in self.providers:
            if p["id"] == self.current_provider_id:
                p["status"] = "offline" if p["status"] == "online" else "online"
        self.providers = self.providers # Trigger state update

    def submit_customer_request(self, service_type: str):
        """Simulate the process of requesting help."""
        self.selected_service = service_type
        self.request_status = "searching"
        # Simulate a match after 3 seconds.
        return rx.set_timeout(self._simulate_match, 3000)

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

    def open_signup(self) -> None:
        self.screen = "signup"
        self.error_message = ""
        self.signup_message = ""

    def open_login(self) -> None:
        self.screen = "login"
        self.error_message = ""
        self.signup_message = ""

    def choose_signup_role(self, role: str) -> None:
        if role in {"client", "provider"}:
            self.signup_role = role

    def set_signup_name(self, value: str) -> None:
        self.signup_name = value

    def set_signup_email(self, value: str) -> None:
        self.signup_email = value

    def set_signup_password(self, value: str) -> None:
        self.signup_password = value

    def submit_signup(self) -> None:
        self.signup_message = ""
        self.error_message = ""
        self.error_message = validate_signup(self.signup_name, self.signup_email, self.signup_password)
        if self.error_message:
            self.signup_password = ""
            return
        self.signup_message = "Cadastro preparado. A conexão com o banco será adicionada na próxima etapa."
        self.signup_password = ""

    def set_email_value(self, value: str) -> None:
        self.email = value

    def set_password_value(self, value: str) -> None:
        self.password = value

    def return_to_presentation(self) -> None:
        self.screen = "presentation"
        self.error_message = ""
        self.signup_message = ""
        self.password = ""
        self.signup_password = ""

    def open_map_test(self) -> None:
        self.screen = "map_test"

    def logout(self) -> None:
        self.screen = "presentation"
        self.auth_token = ""
        self.user_id = None
        self.email = ""
        self.password = ""
        self.signup_name = ""
        self.signup_email = ""
        self.signup_password = ""
        self.error_message = ""
        self.signup_message = ""

    def get_xano_api_url(self) -> str:
        return os.getenv("XANO_API_URL", "").strip().rstrip("/")

    def login(self) -> None:
        """Authenticate through Xano without retaining the submitted password."""
        self.error_message = ""
        self.is_loading = True
        api_url = self.get_xano_api_url()
        if not api_url:
            self.error_message = "O login ainda não está configurado neste ambiente."
            self.password = ""
            self.is_loading = False
            return

        try:
            auth_token, user_id = login_with_xano(self.email, self.password, api_url)
            self.auth_token = auth_token
            self.user_id = user_id
            self.screen = "authenticated"
        except PermissionError:
            self.error_message = "Email ou senha inválidos."
        except (requests.RequestException, ValueError):
            self.error_message = "Não foi possível conectar ao serviço de login. Tente novamente."
        finally:
            self.password = ""
            self.is_loading = False

    def bypass_login_client(self) -> None:
        """Bypass login for testing as a client."""
        self.screen = "authenticated"

    def bypass_login_provider(self) -> None:
        """Bypass login for testing as a provider."""
        self.screen = "provider_dash"


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


def brand_header() -> rx.Component:
    return rx.hstack(
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
                    on_click=AppState.choose_signup_role("client"),
                    class_name=rx.cond(AppState.signup_role == "client", "role-card selected", "role-card"),
                    flex="1",
                ),
                rx.button(
                    rx.vstack(
                        rx.text("Prestador de serviço", weight="bold"),
                        rx.text("Ofereço assistência", class_name="role-detail"),
                        spacing="1",
                        align="start",
                    ),
                    on_click=AppState.choose_signup_role("provider"),
                    class_name=rx.cond(AppState.signup_role == "provider", "role-card selected", "role-card"),
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
                    rx.button("Criar conta", type="submit", class_name="primary-button", width="100%"),
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
                on_submit=AppState.submit_signup,
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
    return rx.center(
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
            rx.vstack(
                rx.text("Acesso Rápido (Teste)", weight="bold", font_size="0.8rem", color=COLORS["muted"], margin_top="2rem"),
                rx.hstack(
                    rx.button(
                        "Testar Cliente",
                        on_click=AppState.bypass_login_client,
                        class_name="secondary-button",
                        size="1",
                    ),
                    rx.button(
                        "Testar Prestador",
                        on_click=AppState.bypass_login_provider,
                        class_name="secondary-button",
                        size="1",
                    ),
                    width="100%",
                    spacing="3",
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            width="min(100%, 38rem)",
            align="start",
            spacing="5",
            class_name="login-panel",
        ),
        min_height="calc(100vh - 8rem)",
        padding="2rem 1rem",
    )


def hero_visual() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("visão da assistência", class_name="visual-label"),
                rx.text("● online", class_name="live-label"),
                justify="between",
                width="100%",
            ),
            rx.box(rx.text("Sua localização atual", class_name="map-label"), class_name="map-preview"),
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
            rx.text("3 opções encontradas", class_name="mini-stats"),
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
        rx.hstack(
            rx.button("Conhecer a SOS Drive", on_click=AppState.open_signup, class_name="primary-button", flex="1"),
            rx.button("Ver mapa (Teste)", on_click=AppState.open_map_test, class_name="secondary-button", flex="1"),
            width="100%",
            spacing="3",
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


def customer_dashboard() -> rx.Component:
    return rx.box(
        # Map Container (Background)
        rx.box(
            rx.html(
                '<div id="customer-map" style="height: 100vh; width: 100vw; position: absolute; top: 0; left: 0; z-index: 0; background: #f3f4f6;"></div>'
                '<script>'
                'function initCustomerMap() {'
                '  var cMap = L.map("customer-map", { zoomControl: false }).setView([-23.5505, -46.6333], 13);'
                '  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "" }).addTo(cMap);'
                '  L.marker([-23.5505, -46.6333], { icon: L.divIcon({ className: "user-marker", html: "🔵" }) }).addTo(cMap).bindPopup("Você está aqui");'
                '  var providers = ['
                '    {name: "João", coords: [-23.5520, -46.6340]},'
                '    {name: "Maria", coords: [-23.5580, -46.6310]},'
                '    {name: "Carlos", coords: [-23.5480, -46.6380]}'
                '  ];'
                '  providers.forEach(p => L.marker(p.coords).addTo(cMap).bindPopup(p.name));'
                '}'
                'setTimeout(initCustomerMap, 100);'
                '</script>',
            ),
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="0",
        ),
        # UI Overlay
        rx.box(
            rx.vstack(
                # Nearby Providers Counter
                rx.box(
                    rx.hstack(
                        rx.text("📍", font_size="1.2rem"),
                        rx.text(
                            f"Existem {OperationalState.online_providers_count} prestadores online perto de você",
                            weight="bold",
                            font_size="0.9rem",
                            color=COLORS["text"],
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name="glass-panel",
                    padding="0.75rem 1.25rem",
                    position="absolute",
                    top="2rem",
                    left="50%",
                    transform="translateX(-50%)",
                    z_index="20",
                    width="auto",
                    pointer_events="auto",
                ),
                # Bottom Sheet for Help Selection
                rx.vstack(
                    rx.text("Do que você precisa?", weight="bold", size="5", margin_bottom="1rem", color=COLORS["text"]),
                    rx.grid(
                        rx.button(
                            rx.vstack(
                                rx.text("🛞", font_size="1.5rem"),
                                rx.text("Pneu Furado", font_size="0.8rem", color=COLORS["text"], weight="bold"),
                            ),
                            on_click=OperationalState.submit_customer_request("tire"),
                            class_name="op-card",
                            width="100%",
                            height="80px",
                            border_radius="16px",
                            cursor="pointer",
                        ),
                        rx.button(
                            rx.vstack(
                                rx.text("🔋", font_size="1.5rem"),
                                rx.text("Bateria", font_size="0.8rem", color=COLORS["text"], weight="bold"),
                            ),
                            on_click=OperationalState.submit_customer_request("battery"),
                            class_name="op-card",
                            width="100%",
                            height="80px",
                            border_radius="16px",
                            cursor="pointer",
                        ),
                        rx.button(
                            rx.vstack(
                                rx.text("🔧", font_size="1.5rem"),
                                rx.text("Mecânica", font_size="0.8rem", color=COLORS["text"], weight="bold"),
                            ),
                            on_click=OperationalState.submit_customer_request("mechanical"),
                            class_name="op-card",
                            width="100%",
                            height="80px",
                            border_radius="16px",
                            cursor="pointer",
                        ),
                        rx.button(
                            rx.vstack(
                                rx.text("⛽", font_size="1.5rem"),
                                rx.text("Combustível", font_size="0.8rem", color=COLORS["text"], weight="bold"),
                            ),
                            on_click=OperationalState.submit_customer_request("fuel"),
                            class_name="op-card",
                            width="100%",
                            height="80px",
                            border_radius="16px",
                            cursor="pointer",
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    # Request Status Overlay
                    rx.cond(
                        OperationalState.request_status == "searching",
                        rx.vstack(
                            rx.text("Buscando prestador...", weight="bold", color=COLORS["text"]),
                            rx.spinner(size="1"),
                            spacing="3",
                            align="center",
                            padding="1rem",
                            width="100%",
                            background="rgba(255,255,255,0.9)",
                            border_radius="16px",
                            margin_top="1rem",
                        ),
                    ),
                    rx.cond(
                        OperationalState.request_status == "matched",
                        rx.vstack(
                            rx.text("Prestador encontrado!", weight="bold", color=COLORS["emergency_orange"]),
                            rx.text("João Socorro está a caminho", font_size="0.9rem", color=COLORS["text"]),
                            rx.button("Cancelar Pedido", on_click=OperationalState.set_request_status("idle"), class_name="secondary-button", size="1"),
                            spacing="3",
                            align="center",
                            padding="1rem",
                            width="100%",
                            background="rgba(255,255,255,0.9)",
                            border_radius="16px",
                            margin_top="1rem",
                        ),
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
                    z_index="20",
                    border="1px solid rgba(255,255,255,0.5)",
                    box_shadow="0 -10px 30px rgba(0,0,0,0.1)",
                    pointer_events="auto",
                ),
                width="100%",
                height="100vh",
                position="absolute",
                top="0",
                left="0",
                z_index="10",
                pointer_events="none",
            ),
        ),
        width="100%",
        height="100vh",
        position="relative",
        overflow="hidden",
    )


def provider_dashboard() -> rx.Component:
    return rx.box(
        # Map Container
        rx.box(
            rx.html(
                '<div id="provider-map" style="height: 100vh; width: 100vw; position: absolute; top: 0; left: 0; z-index: 0; background: #f3f4f6;"></div>'
                '<script>'
                'function initProviderMap() {'
                '  var pMap = L.map("provider-map", { zoomControl: false }).setView([-23.5505, -46.6333], 13);'
                '  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "" }).addTo(pMap);'
                '  L.marker([-23.5505, -46.6333], { icon: L.divIcon({ className: "provider-marker", html: "🛠️" }) }).addTo(pMap).bindPopup("Minha Localização");'
                '  var activeCalls = ['
                '    {id: 101, name: "Motorista A", type: "Pneu Furado", coords: [-23.5520, -46.6340]},'
                '    {id: 102, name: "Motorista B", type: "Bateria", coords: [-23.5580, -46.6310]}'
                '  ];'
                '  activeCalls.forEach(c => L.marker(c.coords).addTo(pMap).bindPopup(`Chamado #${c.id}: ${c.type}`));'
                '}'
                'setTimeout(initProviderMap, 100);'
                '</script>',
            ),
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
            z_index="0",
        ),
        # Overlay UI
        rx.box(
            rx.vstack(
                # Top Bar: Status Toggle
                rx.hstack(
                    rx.box("SOS Drive", weight="bold", font_size="1.2rem", color=COLORS["text"]),
                    rx.hstack(
                        rx.text(
                            rx.cond(OperationalState.providers[0]["status"] == "online", "SOU ONLINE", "SOU OFFLINE"),
                            font_size="0.8rem",
                            weight="bold",
                            color=COLORS["text"],
                        ),
                        rx.checkbox(
                            on_change=OperationalState.toggle_provider_status,
                            checked=rx.cond(OperationalState.providers[0]["status"] == "online", True, False),
                        ),
                        spacing="2",
                        align="center",
                        class_name="glass-panel",
                        padding="0.5rem 1rem",
                    ),
                    justify="between",
                    width="100%",
                    position="absolute",
                    top="2rem",
                    left="2rem",
                    right="2rem",
                    z_index="20",
                    pointer_events="auto",
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
                    z_index="20",
                    border="1px solid rgba(255,255,255,0.5)",
                    box_shadow="0 -10px 30px rgba(0,0,0,0.1)",
                    pointer_events="auto",
                ),
                width="100%",
                height="100vh",
                position="absolute",
                top="0",
                left="0",
                z_index="10",
                pointer_events="none",
            ),
        ),
        width="100%",
        height="100vh",
        position="relative",
        overflow="hidden",
    )


def provider_profile_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text("meu perfil", class_name="section-kicker"),
            rx.heading("Configurações do Prestador", class_name="section-title", size="8"),
            rx.text("Defina suas especialidades para receber os chamados corretos.", class_name="section-intro"),
            rx.vstack(
                # Basic Info
                rx.vstack(
                    rx.text("Informações Básicas", weight="bold", size="4"),
                    rx.vstack(
                        rx.text("Nome", class_name="field-label"),
                        rx.input(
                            value=OperationalState.providers[0]["name"],
                            on_change=lambda v: OperationalState.set_provider_name(v),
                            width="100%",
                            height="3.25rem",
                            padding="0 1rem",
                            border_radius="14px",
                            border=f"1px solid {COLORS['line']}",
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    spacing="3",
                    class_name="op-card",
                    width="100%",
                ),
                # Specialties
                rx.vstack(
                    rx.text("Minhas Especialidades", weight="bold", size="4"),
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
                ),
                rx.button("Salvar Perfil", class_name="primary-button", width="100%"),
                width="min(100%, 32rem)",
                spacing="5",
                align="start",
            ),
            align="center",
            spacing="6",
            padding="2rem 1rem",
        ),
        min_height="calc(100vh - 8rem)",
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


def index() -> rx.Component:
    return rx.cond(
        AppState.screen == "map_test",
        rx.box(map_test_screen(), class_name="app-shell"),
        rx.cond(
            AppState.screen == "provider_dash",
            rx.box(provider_dashboard(), class_name="app-shell"),
            rx.cond(
                AppState.screen == "provider_profile",
                rx.box(provider_profile_screen(), class_name="app-shell"),
                rx.cond(
                    AppState.screen == "signup",
                    rx.box(signup_screen(), class_name="app-shell"),
                    rx.cond(
                        AppState.screen == "login",
                        rx.box(login_screen(), class_name="app-shell"),
                        rx.cond(
                            AppState.screen == "authenticated",
                            rx.box(customer_dashboard(), class_name="app-shell"),
                            rx.box(landing_page(), class_name="app-shell"),
                        ),
                    ),
                ),
            ),
        ),
    )


app = rx.App(
    style=GLOBAL_STYLE,
    head_components=[
        rx.html('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />'),
        rx.html('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'),
    ],
)
app.add_page(index, title="SOS Drive | Assistência quando importa")
