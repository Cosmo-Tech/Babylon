import logging
import os
import sys
import hvac

from typing import Any
from typing import Callable
from functools import wraps
from azure.storage.blob import BlobServiceClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from terrasnek.api import TFC
from .environment import Environment
from .credentials import get_azure_credentials

logger = logging.getLogger("Babylon")
env = Environment()


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
