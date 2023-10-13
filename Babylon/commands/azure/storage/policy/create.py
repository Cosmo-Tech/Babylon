import logging
from typing import Any
from click import argument, command, option
from Babylon.utils.clients import pass_storage_mgmt_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from azure.mgmt.storage import StorageManagementClient

from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_storage_mgmt_client
@argument("account_name", type=QueryType())
@option("--days", type=int, default=365, help="Days after last modification", show_default=True)
@inject_context_with_resource({"azure": ['resource_group_name', 'storage_account_name']})
def create(context: Any, storage_mgmt_client: StorageManagementClient, days: int, account_name: str) -> CommandResponse:
    """
    Create or update default policy storage account
    """
    if account_name is None:
        logger.info(f"Account Name: {context['azure_resource_group_name']}")
    resource_group = context['azure_resource_group_name']
    account_name = account_name or context['azure_storage_account_name']
    s = storage_mgmt_client.management_policies.create_or_update(
        resource_group, account_name, "default", {
            "policy": {
                "rules": [{
                    "enabled": True,
                    "name": f"csm{days}days",
                    "type": "Lifecycle",
                    "definition": {
                        "filters": {
                            "blob_types": ["blockBlob"]
                        },
                        "actions": {
                            "base_blob": {
                                "delete": {
                                    "days_after_modification_greater_than": days
                                }
                            },
                            "snapshot": {
                                "delete": {
                                    "days_after_creation_greater_than": days
                                }
                            },
                            "version": {
                                "delete": {
                                    "days_after_creation_greater_than": days
                                }
                            }
                        }
                    }
                }]
            }
        })
    logger.info(f"Successfully created policy {s}")
    return CommandResponse.success()
