from __future__ import annotations

"""SOS Drive Reflex application."""


import reflex as rx
import requests
import os
import math
import time
import asyncio

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


class AppState(rx.State):
    """Application state for navigation and driver authentication."""

    screen: str = "presentation"
    user_role: str = "client" # Added to track role
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
    active_call_status: str | None = None
    active_call_eta: str = "15 min"

    # Profile Fields (Mock)
    user_profile_photo: str = ""
    user_full_name: str = "Usuário SOS"
    user_email: str = "usuario@exemplo.com"
    user_phone: str = "(11) 99999-9999"

    @rx.var
    def user_initials(self) -> str:
        """Compute initials from user_full_name."""
        names = self.user_full_name.split()
        if not names:
            return "U"
        first = names[0][0].upper()
        last = names[-1][0].upper() if len(names) > 1 else ""
        return f"{first}{last}"

    def open_signup(self) -> None:
        return rx.redirect("/signup")

    def open_login(self) -> None:
        return rx.redirect("/login")

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
        return rx.redirect("/")

    def open_map_test(self) -> None:
        return rx.redirect("/test-map")

    def logout(self) -> None:
        self.auth_token = ""
        self.user_id = None
        self.email = ""
        self.password = ""
        self.signup_name = ""
        self.signup_email = ""
        self.signup_password = ""
        self.error_message = ""
        self.signup_message = ""
        return rx.redirect("/")

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
            return rx.redirect("/home")
        except PermissionError:
            self.error_message = "Email ou senha inválidos."
        except (requests.RequestException, ValueError):
            self.error_message = "Não foi possível conectar ao serviço de login. Tente novamente."
        finally:
            self.password = ""
            self.is_loading = False

    def bypass_login_client(self) -> None:
        """Bypass login for testing as a client."""
        self.user_role = "client"
        return rx.redirect("/home")

    def bypass_login_provider(self) -> None:
        """Bypass login for testing as a provider."""
        self.user_role = "provider"
        return rx.redirect("/home")

    def set_user_full_name(self, value: str) -> None:
        self.user_full_name = value

    def set_user_email(self, value: str) -> None:
        self.user_email = value

    def set_user_phone(self, value: str) -> None:
        self.user_phone = value

    def handle_profile_upload(self):
        """Mock upload handler: just sets a placeholder image."""
        # In a real app, we'd handle the upload via rx.upload
        # For mock, we just use a sample image.
        self.user_profile_photo = "https://i.pravatar.cc/300"



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
    available_requests: list[dict] = [
        {
            "id": 201,
            "type": "Combustível",
            "service_icon": "⛽",
            "user": "Pedro Lima",
            "phone": "(11) 98888-1111",
            "vehicle": "Toyota Corolla - ABC-1234",
            "note": "Estou no acostamento, sem risco imediato.",
            "distance": "4.1 km",
            "eta": "9 min",
            "address": "Av. Paulista, 1578 - Bela Vista, São Paulo",
            "coords": [-23.5614, -46.6559],
            "maps_url": "https://www.google.com/maps/dir/?api=1&destination=-23.5614,-46.6559",
        },
        {
            "id": 202,
            "type": "Troca de Pneu",
            "service_icon": "🛞",
            "user": "Ana Souza",
            "phone": "(11) 97777-2222",
            "vehicle": "Fiat Mobi - QWE-9087",
            "note": "Pneu dianteiro esquerdo furou ao sair do estacionamento.",
            "distance": "2.8 km",
            "eta": "6 min",
            "address": "Rua Haddock Lobo, 400 - Cerqueira César, São Paulo",
            "coords": [-23.5588, -46.6621],
            "maps_url": "https://www.google.com/maps/dir/?api=1&destination=-23.5588,-46.6621",
        },
    ]
    selected_request: dict = {}
    atendimento_mock: dict = {}
    atendimento_phase: str = ""
    show_cancel_confirm: bool = False


    # Customer Request state
    selected_service: str | None = None
    request_status: str = "idle" # idle, searching, matched

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

    def close_vehicle_modal(self):
        self.show_vehicle_modal = False
        self.editing_vehicle_id = None

    def save_vehicle(self):
        """Save vehicle data (create or update)."""
        if not self.v_plate or not self.v_brand or not self.v_model:
            return # Simple validation

        if self.editing_vehicle_id:
            self.update_vehicle(self.editing_vehicle_id, self.v_brand, self.v_model, self.v_plate, self.v_year, self.v_color)
        else:
            self.add_vehicle(self.v_brand, self.v_model, self.v_plate, self.v_year, self.v_color)

        self.close_vehicle_modal()


    def toggle_provider_status(self):
        """Toggle status of the current simulated provider."""
        self.is_available = not self.is_available
        for p in self.providers:
            if p["id"] == self.current_provider_id:
                p["status"] = "offline" if p["status"] == "online" else "online"
        self.providers = self.providers # Trigger state update

    def accept_request(self, request_id: int):
        """Select a request and start local/mock attendance flow."""
        request = next((item for item in self.available_requests if item["id"] == request_id), None)
        if request is None:
            return rx.toast("Solicitação não encontrada.")
        self.selected_request = request
        provider = next((item for item in self.providers if item["id"] == self.current_provider_id), None)
        provider_coords = provider["coords"] if provider else [-23.5505, -46.6333]
        self.atendimento_mock = build_atendimento_mock(request, provider_coords)
        self.atendimento_phase = "A_CAMINHO"
        self.show_cancel_confirm = False
        self.available_requests = [item for item in self.available_requests if item["id"] != request_id]
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

    def confirm_cancel_atendimento(self):
        """Cancel attendance, clear mock and return to provider home."""
        self.reset_atendimento()
        return rx.redirect("/home_provider")

    def advance_atendimento_phase(self):
        """Advance through mock attendance phases in strict sequence."""
        if self.atendimento_phase == "A_CAMINHO":
            self.atendimento_phase = "NO_LOCAL"
            return
        if self.atendimento_phase == "NO_LOCAL":
            self.atendimento_phase = "ATENDENDO"
            return
        if self.atendimento_phase == "ATENDENDO":
            self.atendimento_phase = "CONCLUIDO"
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

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate the great circle distance between two points in km."""
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

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
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "✏️",
                    on_click=lambda: OperationalState.open_vehicle_modal(v["id"]),
                    class_name="glass-panel",
                    padding="0.4rem",
                    border_radius="8px",
                    width="2.2rem",
                    height="2.2rem",
                ),
                rx.button(
                    "🗑️",
                    on_click=lambda: OperationalState.delete_vehicle(v["id"]),
                    class_name="glass-panel",
                    padding="0.4rem",
                    border_radius="8px",
                    width="2.2rem",
                    height="2.2rem",
                ),
                spacing="2",
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
                    rx.text("O especialista já foi notificado e está a caminho.", font_size="0.9rem", color=COLORS["text"], text_align="center"),
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
        on_mount=rx.call_script(
            "navigator.geolocation.getCurrentPosition((pos) => { "
            "const { latitude: lat, longitude: lng } = pos.coords; "
            "window.updateUserMarker('customer-map', lat, lng); "
            "window.triggerReflexUpdate({ role: 'client', lat: lat, lng: lng }); "
            "});"
        ),
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
            on_mount=rx.call_script(
                "window.initSOSMap('provider-map', [-23.5505, -46.6333], 13);"
            ),
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
                    rx.cond(OperationalState.providers[0]["status"] == "online", "SOU ONLINE", "SOU OFFLINE"),
                    font_size="0.8rem",
                    weight="bold",
                    color=COLORS["text"],
                ),
                rx.checkbox(
                    on_change=OperationalState.toggle_provider_status,
                    checked=rx.cond(OperationalState.providers[0]["status"] == "online", True, False),
                ),
                spacing="3",
                align="center",
                class_name="glass-panel",
                padding="0.5rem 1rem",
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
    """Unified profile screen for both clients and providers."""
    return rx.center(
        rx.vstack(
            # Top Navigation / Back Button
            rx.hstack(
                rx.button(
                    rx.hstack(rx.text("←", font_size="1.2rem"), rx.text("Voltar")),
                    on_click=rx.redirect("/home"),
                    class_name="secondary-button",
                    size="1",
                ),
                justify="start",
                width="100%",
                margin_bottom="2rem",
            ),
            # Header Section
            rx.vstack(
                rx.text("meu perfil", class_name="section-kicker"),
                rx.heading("Configurações de Perfil", class_name="section-title", size="8"),
                rx.text("Mantenha seus dados atualizados para melhor assistência.", class_name="section-intro"),
                align="start",
                spacing="2",
                width="100%",
            ),
            # Main Content Area
            rx.vstack(
                # Profile Header with Avatar and Upload
                rx.vstack(
                    rx.box(
                        rx.cond(
                            AppState.user_profile_photo != "",
                            rx.image(src=AppState.user_profile_photo, width="100%", height="100%", border_radius="50%", object_fit="cover"),
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
                    ),
                    rx.button(
                        "Alterar Foto",
                        on_click=AppState.handle_profile_upload,
                        class_name="secondary-button",
                        size="1",
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
                        rx.text("Email", class_name="field-label"),
                        rx.input(
                            value=AppState.user_email,
                            on_change=AppState.set_user_email,
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
                    AppState.user_role == "provider",
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
                            on_click=lambda: OperationalState.open_vehicle_modal(),
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
                rx.button("Salvar Perfil", class_name="primary-button", width="100%"),
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
        background="white",
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
            AppState.user_role == "provider",
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
                rx.text("Status:", weight="bold"),
                rx.checkbox(
                    checked=OperationalState.is_available,
                    on_change=OperationalState.toggle_provider_status,
                ),
                rx.text(
                    rx.cond(OperationalState.is_available, "Disponível", "Indisponível"),
                    weight="bold",
                    color=rx.cond(OperationalState.is_available, "#22C55E", "#EF4444"),
                ),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            profile_avatar(),
            position="absolute",
            top="2rem",
            left="2rem",
            right="2rem",
            z_index="100",
            align="center",
        ),
        # Main Body (50/50 Split)
        rx.vstack(
            # Upper Half: Map
            rx.box(
                id="provider-home-map",
                width="100%",
                height="50vh",
                position="relative",
                on_mount=rx.call_script(
                    "window.initSOSMap('provider-home-map', [-23.5505, -46.6333], 13);"
                ),
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
        on_mount=OperationalState.reset_provider_home,
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
        rx.box(
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
            rx.text(
                rx.cond(
                    OperationalState.atendimento_mock,
                    f"Distância {OperationalState.atendimento_mock['distance']} • ETA {OperationalState.atendimento_mock['eta']}",
                    "Distância 0.0 km • ETA 0 min",
                ),
                font_size="0.85rem",
                color=COLORS["muted"],
            ),
            class_name="glass-panel",
            border_radius="14px",
            padding="0.7rem 0.9rem",
            position="absolute",
            top="5rem",
            left="50%",
            transform="translateX(-50%)",
            z_index="110",
            width="auto",
        ),
        rx.vstack(
            rx.box(
                rx.vstack(
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
                                font_size="1rem",
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
                    rx.vstack(
                        rx.text("Veículo", class_name="field-label"),
                        rx.text(
                            rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["veiculo"], "Não informado"),
                            color=COLORS["text"],
                        ),
                        rx.text("Endereço", class_name="field-label"),
                        rx.text(
                            rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["endereco"], "Não informado"),
                            color=COLORS["text"],
                        ),
                        rx.text("Observação", class_name="field-label"),
                        rx.text(
                            rx.cond(OperationalState.atendimento_mock, OperationalState.atendimento_mock["observacao"], "Sem observações."),
                            color=COLORS["muted"],
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.cond(
                            OperationalState.can_cancel_atendimento,
                            rx.button(
                                "Cancelar atendimento",
                                on_click=OperationalState.open_cancel_confirm,
                                class_name="secondary-button",
                                flex="1",
                            ),
                        ),
                        rx.button(
                            OperationalState.atendimento_next_action_label,
                            on_click=OperationalState.advance_atendimento_phase,
                            class_name="primary-button",
                            flex="1",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    spacing="4",
                    width="100%",
                ),
                class_name="op-card",
                width="100%",
                max_width="42rem",
            ),
            width="100%",
            align="center",
            position="absolute",
            left="0",
            right="0",
            bottom="1rem",
            z_index="120",
            padding_x="1rem",
        ),
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


app = rx.App(
    style=GLOBAL_STYLE,
    head_components=[
        rx.html('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />'),
        rx.html('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'),
        rx.html('''
        <script>
        window.sosMaps = {};
        window.sosMarkers = {};
        window.sosUserMarkers = {};

        window.initSOSMap = function(id, center, zoom) {
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

        window.showSOSRoute = function(mapId, startCoords, endCoords) {
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

            window.sosRouteLine = L.polyline([start, end], {
                color: "#F97316",
                weight: 5,
                opacity: 0.85,
            }).addTo(map);

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
        </script>
        '''),
    ],
)
app.add_page(index, route="/", title="SOS Drive | Assistência quando importa")
app.add_page(home_screen, route="/home", title="Home | SOS Drive")
app.add_page(user_home_screen, route="/home_client", title="Home Cliente | SOS Drive")
app.add_page(signup_screen, route="/signup", title="Cadastro | SOS Drive")
app.add_page(login_screen, route="/login", title="Login | SOS Drive")
app.add_page(customer_dashboard, route="/customer", title="Dashboard Cliente | SOS Drive")
app.add_page(provider_dashboard, route="/provider", title="Dashboard Prestador | SOS Drive")
app.add_page(provider_home_screen, route="/home_provider", title="Solicitações Próximas | SOS Drive")
app.add_page(service_details_screen, route="/service-details", title="Detalhes do Atendimento | SOS Drive")
app.add_page(provider_service_progress_screen, route="/provider-service-progress", title="Atendimento em Andamento | SOS Drive")
app.add_page(service_finalized_screen, route="/service-finalized", title="Chamado Finalizado | SOS Drive")
app.add_page(profile_screen, route="/profile", title="Meu Perfil | SOS Drive")
app.add_page(map_test_screen, route="/test-map", title="Teste de Mapa | SOS Drive")
