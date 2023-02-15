import logging

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
