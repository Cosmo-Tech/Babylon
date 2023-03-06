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

from .environment import Environment
from .credentials import get_azure_credentials
from .credentials import get_azure_token

logger = logging.getLogger("Babylon")


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
