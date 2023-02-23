import logging
from functools import wraps
from typing import Any
from typing import Callable

from azure.mgmt.kusto import KustoManagementClient
import cosmotech_api
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

from .environment import Environment

logger = logging.getLogger("Babylon")

SCOPES = {
    "graph": "https://graph.microsoft.com/.default",
    "default": "https://management.azure.com/.default",
    "powerbi": "https://analysis.windows.net/powerbi/api/.default",
    "csm_api": Environment().configuration.get_platform_var("api_scope")
}


def get_azure_token(scope: str = "default") -> str:
    """Returns an azure token"""
    # Getting scope url from utils.scope
    credentials = get_azure_credentials()
    scope_url = SCOPES[scope.lower()]
    logger.debug(f"Getting azure token with scope {scope_url}")
    try:
        token = credentials.get_token(scope_url)
    except ClientAuthenticationError:
        logger.error(f"Could not get token with scope {scope_url}")
        raise ConnectionError(f"Could not connect to Azure API with scope {scope_url}")
    return token.token


def get_azure_credentials() -> DefaultAzureCredential:
    """Logs to Azure and saves the token as a config variable"""
    env = Environment()
    azure_tenant_id = env.configuration.get_platform_var("azure_tenant_id")
    return DefaultAzureCredential(exclude_interactive_browser_credential=False,
                                  interactive_browser_tenant_id=azure_tenant_id,
                                  shared_cache_tenant_id=azure_tenant_id,
                                  visual_studio_code_tenant_id=azure_tenant_id)


def pass_api_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        azure_token = get_azure_token("csm_api")
        api_url = Environment().configuration.get_platform_var("api_url")
        api_configuration = cosmotech_api.Configuration(host=api_url,
                                                        discard_unknown_keys=True,
                                                        access_token=azure_token)
        kwargs["api_client"] = cosmotech_api.ApiClient(api_configuration)
        return func(*args, **kwargs)

    return wrapper


def pass_kusto_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        azure_subscription = Environment().configuration.get_platform_var("azure_subscription")
        azure_credential = get_azure_credentials()
        kwargs["kusto_client"] = KustoManagementClient(credential=azure_credential, subscription_id=azure_subscription)
        return func(*args, **kwargs)

    return wrapper


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
