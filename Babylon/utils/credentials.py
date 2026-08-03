import logging
from functools import wraps
from typing import Any, Callable

import requests

from Babylon.utils.response import CommandResponse

from .environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


def get_superset_token(base_url: str, config: dict) -> str | None:
    """
    Obtain a Superset-internal JWT for machine-to-machine API access.

    Uses ``provider: db`` (the only provider supported by Superset's REST login
    endpoint) with a local service-account whose credentials are expected in
    ``config`` under the keys ``superset_admin_username`` / ``superset_admin_password``

    These keys must be present in the ``keycloak-babylon`` K8s secret.

    Args:
        base_url (str): Superset base URL (e.g. https://superset-<cluster>.<domain>).
        config (dict): Config dict from the K8s secret (via ``env.retrieve_config()``).
    Returns:
        str: Superset JWT access_token, or None on failure.
    """
    username = config.get("superset_admin_username") or ""
    password = config.get("superset_admin_password") or ""

    if not username or not password:
        logger.error("  [bold red]✘[/bold red] Superset admin credentials not found in config. ")
        return None

    url = f"{base_url.rstrip('/')}/api/v1/security/login"
    payload = {
        "username": username,
        "password": password,
        "provider": "db",
        "refresh": True,
    }

    try:
        logger.debug(f"  [dim]→ Authenticating to Superset (db provider) at {url}[/dim]")
        response = requests.post(url, json=payload, timeout=10)
        if not response.ok:
            logger.error(f"  [bold red]✘[/bold red] Superset login failed ({response.status_code}): {response.text}")
            return None

        token = response.json().get("access_token")
        if not token:
            logger.error("  [bold red]✘[/bold red] access_token not found in Superset login response")
            return None

        logger.debug("  [bold green]✔[/bold green] Superset JWT obtained successfully")
        return token

    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Could not authenticate to Superset: {exp}")
        return None


def get_keycloak_credentials() -> tuple[dict, dict]:
    """ "Logs to keycloak and saves the token as a config variable"""
    try:
        config = env.retrieve_config()
        client_id = config.get("keycloak_client_id")
        client_secret = config.get("keycloak_client_secret")
        credentials = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        }
        if not all(credentials.values()):
            missing = [k for k, v in credentials.items() if not v]
            raise AttributeError(f"  [bold red]✘[/bold red] Missing required Keycloak credentials: {', '.join(missing)}")

        return credentials, config

    except KeyError as e:
        logger.error(f"  [bold red]✘[/bold red] Check the Keycloak configuration in the Kubernetes secret: {e}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error while retrieving Keycloak credentials: {e}")


def get_keycloak_token() -> tuple[str, dict]:
    """Returns keycloak token"""
    try:
        credentials, config = get_keycloak_credentials()
        url = config["keycloak_token_url"]
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        response = requests.post(url=url, data=credentials, headers=headers, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get(
            "access_token",
        )
        if not access_token:
            logger.error("  [bold red]✘[/bold red] Access token not found in Keycloak response")
        return access_token, config

    except requests.exceptions.RequestException as e:
        logger.error(f"  [bold red]✘[/bold red] Keycloak request failed: {e}")


def pass_keycloak_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab keycloak credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["keycloak_credentials"] = get_keycloak_credentials()
        return func(*args, **kwargs)

    return wrapper


def pass_keycloak_token() -> Callable[..., Any]:
    """Logs to keycloak and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                token, config = get_keycloak_token()
                kwargs["keycloak_token"] = token
                kwargs["config"] = config
            except ConnectionError:
                return CommandResponse().fail()
            return func(*args, **kwargs)

        return wrapper

    return wrap_function
