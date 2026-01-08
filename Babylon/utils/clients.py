import logging
from functools import wraps
from typing import Any, Callable

from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient

from .credentials import get_azure_credentials
from .environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


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


def pass_iam_client(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab iam client"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = env.get_state_from_vault_by_platform(env.environ_id)
        azure_subscription = state["azure"]["subscription_id"]
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
        azure_subscription = state["azure"]["subscription_id"]
        authorization_client = StorageManagementClient(
            credential=get_azure_credentials(),
            base_url="https://management.azure.com",
            subscription_id=azure_subscription,
        )
        kwargs["storage_mgmt_client"] = authorization_client
        return func(*args, **kwargs)

    return wrapper
