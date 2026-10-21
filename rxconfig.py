"""Reflex project configuration for SOS Drive."""

import ipaddress
import os

import reflex as rx


demo_host = os.getenv("SOSDRIVE_DEMO_HOST", "").strip()
demo_config = {}
if demo_host:
    try:
        demo_ip = ipaddress.ip_address(demo_host)
    except ValueError as error:
        raise ValueError("SOSDRIVE_DEMO_HOST must be a LAN IP address.") from error
    if not isinstance(demo_ip, ipaddress.IPv4Address):
        raise ValueError("SOSDRIVE_DEMO_HOST must be an IPv4 LAN address.")

    demo_config = {
        "api_url": f"http://{demo_ip}:8000",
        "deploy_url": f"http://{demo_ip}:3000",
        "vite_allowed_hosts": [str(demo_ip)],
    }

config = rx.Config(
    app_name="sosdrive_app",
    **demo_config,
)
