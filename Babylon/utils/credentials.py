import logging
from functools import wraps
from typing import Any
from typing import Callable

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import ClientSecretCredential

from .environment import Environment

logger = logging.getLogger("Babylon")


def get_azure_token(scope: str = "default") -> str:
    """Returns an azure token"""
    # Getting scope url from utils.scope
    SCOPES = {
        "graph": "https://graph.microsoft.com/.default",
        "default": "https://management.azure.com/.default",
        "powerbi": Environment().configuration.get_deploy_var("powerbi_api_scope"),
        "csm_api": Environment().configuration.get_platform_var("api_scope")
    }
    credentials = get_azure_credentials()
    scope_url = SCOPES[scope.lower()]
    logger.debug(f"Getting azure token with scope {scope_url}")
    try:
        token = credentials.get_token(scope_url)
    except ClientAuthenticationError:
        logger.error(f"Could not get token with scope {scope_url}")
        raise ConnectionError(f"Could not connect to Azure API with scope {scope_url}")
    return token.token


def get_azure_credentials() -> Any:
    """Logs to Azure and saves the token as a config variable"""
    env = Environment()
    azure_tenant_id = env.configuration.get_platform_var("azure_tenant_id")
    cached_credentials = env.convert_data_query("%secrets%azure")
    try:
        return ClientSecretCredential(cached_credentials["tenant_id"], cached_credentials["client_id"],
                                      cached_credentials["client_secret"])
    except (KeyError, TypeError):
        pass
    return DefaultAzureCredential(shared_cache_tenant_id=azure_tenant_id, visual_studio_code_tenant_id=azure_tenant_id)


def pass_azure_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab Azure credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["azure_credentials"] = get_azure_credentials()
        return func(*args, **kwargs)

    return wrapper


def pass_azure_token(scope: str = "default") -> Callable[..., Any]:
    """Logs to Azure and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            kwargs["azure_token"] = get_azure_token(scope)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function
