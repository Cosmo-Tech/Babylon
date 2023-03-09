import logging
from functools import wraps
from typing import Any
from typing import Callable

from azure.storage.blob import BlobServiceClient
from azure.digitaltwins.core import DigitalTwinsClient
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.kusto import KustoManagementClient
from azure.containerregistry import ContainerRegistryClient
from terrasnek.api import TFC
import cosmotech_api
import docker

from .environment import Environment
from .credentials import get_azure_credentials
from .credentials import get_azure_token
from .request import oauth_request

logger = logging.getLogger("Babylon")


def get_registry_client(registry: str):
    """Gets a Container registry client

    :param registry: registry name: myregistry.azurecr.io
    :type registry: str
    :return: ContainerRegistryClient logger to the registry
    """
    return ContainerRegistryClient(f"https://{registry}",
                                   get_azure_credentials(),
                                   audience="https://management.azure.com")


def get_docker_client(registry: str):
    """Gets a docker client logged to the registry

    :param registry: registry name: myregistry.azurecr.io
    :type registry: str
    :return: Docker client
    """
    # Getting Refresh token
    tenant_id = Environment().convert_data_query("%platform%azure_tenant_id")
    body = f"grant_type=access_token&service={registry}&tenant={tenant_id}&access_token={get_azure_token()}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = oauth_request(f"https://{registry}/oauth2/exchange",
                             get_azure_token(),
                             data=body,
                             type="POST",
                             headers=headers)
    if response is None:
        logger.error(f"Could not get a refresh token for container registry {registry}")
        return None
    # Login to registry with docker
    client = docker.from_env()
    try:
        client.login(username="00000000-0000-0000-0000-000000000000",
                     password=response.json().get("refresh_token"),
                     registry=registry)
    except docker.errors.APIError:
        logger.error(f"Could not connect to container registry {registry}")
        return None
    return client


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
        tf_token = env.convert_data_query("%secrets%terraform.token")
        tf_url = env.working_dir.get_yaml_key("terraform_cloud.yaml", "url")
        tf_organization = env.working_dir.get_yaml_key("terraform_cloud.yaml", "organization")
        api = TFC(tf_token, tf_url)
        api.set_org(tf_organization)
        kwargs["tfc_client"] = api
        return func(*args, **kwargs)

    return wrapper
