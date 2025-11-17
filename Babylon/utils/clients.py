import logging
import os
import sys
import docker
import hvac

from typing import Any
from typing import Callable
from functools import wraps
from azure.storage.blob import BlobServiceClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.kusto import KustoManagementClient
from azure.containerregistry import ContainerRegistryClient
from terrasnek.api import TFC
from .environment import Environment
from .credentials import get_azure_credentials
from .credentials import get_azure_token
from .request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


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
    body = f"grant_type=access_token&service={registry}&tenant={env.tenant_id}&access_token={get_azure_token()}"
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


def pass_hvac_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab hvac client"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        client = None
        try:
            client = hvac.Client(url=env.server_id, token=os.environ.get('BABYLON_TOKEN'))
            if not client.is_authenticated():
                logger.info("Forbidden. Check your credentials")
                sys.exit(1)
        except Exception as e:
            logger.info(e)
            client = None
        kwargs["hvac_client"] = client
        return func(*args, **kwargs)

    return wrapper


def pass_kusto_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab kusto configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        azure_subscription = state['azure']["subscription_id"]
        azure_credential = get_azure_credentials()
        kwargs["kusto_client"] = KustoManagementClient(credential=azure_credential, subscription_id=azure_subscription)
        return func(*args, **kwargs)

    return wrapper


def pass_arm_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab arm mgmt configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        azure_subscription_id = state["azure"]["subscription_id"]
        azure_credential = get_azure_credentials()
        kwargs["arm_client"] = ResourceManagementClient(azure_credential, azure_subscription_id)
        return func(*args, **kwargs)

    return wrapper


def pass_blob_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab api configuration"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        account_name = state["azure"]["storage_account_name"]
        account_secret = env.get_platform_secret(platform=env.environ_id, resource="storage", name="account")
        prefix = f"DefaultEndpointsProtocol=https;AccountName={account_name}"
        connection_str = f"{prefix};AccountKey={account_secret};EndpointSuffix=core.windows.net"
        kwargs["blob_client"] = BlobServiceClient.from_connection_string(connection_str)
        return func(*args, **kwargs)

    return wrapper


def pass_tfc_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab Azure credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = env.get_global_secret(resource="tfc", name="token")
        url = env.get_global_secret(resource="tfc", name="url")
        organization = env.get_global_secret(resource="tfc", name="organization")
        api = TFC(token, url)
        api.set_org(organization)
        kwargs["tfc_client"] = api
        return func(*args, **kwargs)

    return wrapper


def pass_iam_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab iam client"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        azure_subscription = state['azure']["subscription_id"]
        authorization_client = AuthorizationManagementClient(
            credential=get_azure_credentials(),
            subscription_id=azure_subscription,
        )
        kwargs["iam_client"] = authorization_client
        return func(*args, **kwargs)

    return wrapper


def pass_storage_mgmt_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab storage mgmt client"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        azure_subscription = state['azure']["subscription_id"]
        authorization_client = StorageManagementClient(
            credential=get_azure_credentials(),
            base_url="https://management.azure.com",
            subscription_id=azure_subscription,
        )
        kwargs["storage_mgmt_client"] = authorization_client
        return func(*args, **kwargs)

    return wrapper
