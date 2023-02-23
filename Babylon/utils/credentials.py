import logging
from functools import wraps
from typing import Any
from typing import Callable

from azure.storage.blob import BlobServiceClient
from azure.digitaltwins.core import DigitalTwinsClient
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.kusto import KustoManagementClient
from terrasnek.api import TFC
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


def pass_adt_management_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        azure_subscription = Environment().configuration.get_platform_var("azure_subscription")
        azure_credential = get_azure_credentials()
        kwargs["adt_management_client"] = AzureDigitalTwinsManagementClient(azure_credential, azure_subscription)
        return func(*args, **kwargs)

    return wrapper


def pass_adt_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        digital_twin_url = Environment().configuration.get_deploy_var("digital_twin_url")
        azure_credential = get_azure_credentials()
        kwargs["adt_client"] = DigitalTwinsClient(credential=azure_credential, endpoint=digital_twin_url)
        return func(*args, **kwargs)

    return wrapper


def pass_arm_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        azure_subscription = Environment().configuration.get_platform_var("azure_subscription")
        azure_credential = get_azure_credentials()
        kwargs["arm_client"] = ResourceManagementClient(azure_credential, azure_subscription)
        return func(*args, **kwargs)

    return wrapper


def pass_blob_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        account_name = Environment().configuration.get_platform_var("storage_account_name")
        azure_credential = get_azure_credentials()
        account_url = f"https://{account_name}.blob.core.windows.net"
        kwargs["blob_client"] = BlobServiceClient(account_url, azure_credential)
        return func(*args, **kwargs)

    return wrapper


def pass_tfc_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab Azure credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        env = Environment()
        tf_token = env.working_dir.get_yaml_key(".secrets.yaml", "terraform.token")
        tf_url = env.working_dir.get_yaml_key("terraform_cloud.yaml", "url")
        tf_organization = env.working_dir.get_yaml_key("terraform_cloud.yaml", "organization")
        api = TFC(tf_token, tf_url)
        api.set_org(tf_organization)
        kwargs["tfc_client"] = api
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
