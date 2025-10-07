import sys
import logging
import requests

from functools import wraps
from typing import Callable
from typing import Any
from click import option
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import ClientSecretCredential
from azure.identity import CredentialUnavailableError
from azure.identity import DefaultAzureCredential
from Babylon.utils.checkers import check_email
from Babylon.utils.response import CommandResponse
from .environment import Environment


logger = logging.getLogger("Babylon")
env = Environment()


def get_default_powerbi_token():
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
        return token.token
    except Exception as exp:
        logger.info(exp)
        return None


def get_powerbi_token(email: str = None) -> str:
    """Returns an powerbi token"""
    if email:
        access_token = env.get_access_token_with_refresh_token(username=email, internal_scope="powerbi")
        return access_token
    credentials = get_azure_credentials()
    env.AZURE_SCOPES.update({"powerbi": "https://analysis.windows.net/powerbi/api/.default"})
    logger.debug(f"Getting azure token with scope {env.AZURE_SCOPES['powerbi']}")
    try:
        token = credentials.get_token(env.AZURE_SCOPES["powerbi"])
    except ClientAuthenticationError:
        logger.error(f"Could not get token with scope {env.AZURE_SCOPES['powerbi']}")
        sys.exit(1)
    return token.token


def get_azure_token(scope: str = "default") -> str:
    """Returns an azure token"""
    credentials = get_azure_credentials()
    config = env.get_state_from_vault_by_platform(env.environ_id)
    api = config["api"]
    env.AZURE_SCOPES.update({"csm_api": api["scope"]})
    scope_url = env.AZURE_SCOPES[scope.lower()]
    logger.debug(f"Getting azure token with scope {scope_url}")
    try:
        token = credentials.get_token(scope_url)
    except ClientAuthenticationError:
        logger.error(f"Could not get token with scope {scope_url}")
        sys.exit(1)
    return token.token


def get_azure_credentials() -> ClientSecretCredential:
    """Logs to Azure and saves the token as a config variable"""
    credential = None
    config = env.get_state_from_vault_by_platform(env.environ_id)
    babylon_client_id = config["babylon"]["client_id"]
    try:
        baby_client_secret = env.get_env_babylon(name="client", environ_id=env.environ_id)
        credential = ClientSecretCredential(
            client_id=babylon_client_id,
            tenant_id=env.tenant_id,
            client_secret=baby_client_secret,
        )
        if credential is None:
            logger.error("Authentication error during logging to Azure")
            raise AttributeError
    except (CredentialUnavailableError, AttributeError) as exp:
        logger.error(exp)
    return credential


def get_keycloak_credentials() -> dict:
    """"Logs to keycloak and saves the token as a config variable"""
    try:
        config = env.get_state_from_vault_by_platform(env.environ_id)
        credential = {
            "grant_type": config["keycloak"]["grant_type"],
            "client_id": config["keycloak"]["client_id"],
            "client_secret": config["keycloak"]["client_secret"],
            "scope": config["keycloak"]["scope"]
        }
        if not all(credential.values()):
            missing = [k for k, v in credential.items() if not v]
            raise AttributeError(f"Missing required Keycloak credentials: {', '.join(missing)}")

        return credential

    except KeyError as e:
        error_msg = f"Missing Keycloak configuration in Vault: {str(e)}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error getting Keycloak credentials: {str(e)}"
        logger.error(error_msg)


def get_keycloak_token() -> str:
    """Returns keycloak token"""
    config = env.get_state_from_vault_by_platform(env.environ_id)
    url = config["keycloak"]["url"]
    try:
        credentials = get_keycloak_credentials()

        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        response = requests.post(url=url, data=credentials, headers=headers, timeout=30)

        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get("access_token", )
        if not access_token:
            logger.error("Access token not found in Keycloak response")
        return access_token

    except requests.exceptions.RequestException as e:
        logger.error(f"Keycloak request failed: {e}")


def pass_azure_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab Azure credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["azure_credentials"] = get_azure_credentials()
        return func(*args, **kwargs)

    return wrapper


def pass_keycloak_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab keycloak credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["keycloak_credentials"] = get_keycloak_credentials()
        return func(*args, **kwargs)

    return wrapper


def pass_powerbi_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab powerbi credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["powerbi_credentials"] = get_azure_token()
        return func(*args, **kwargs)

    return wrapper


def pass_azure_token(scope: str = "default") -> Callable[..., Any]:
    """Logs to Azure and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                kwargs["azure_token"] = get_azure_token(scope)
            except ConnectionError:
                return CommandResponse().fail()
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def pass_keycloak_token() -> Callable[..., Any]:
    """Logs to keycloak and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                kwargs["keycloak_token"] = get_keycloak_token()
            except ConnectionError:
                return CommandResponse().fail()
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def pass_powerbi_token() -> Callable[..., Any]:
    """Logs to powerbi and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option("--email", "email", help="User email")
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            email = kwargs.pop("email", None)
            if email:
                check_email(email)
            kwargs["powerbi_token"] = get_powerbi_token(email)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function
