import logging

from azure.mgmt.storage import StorageManagementClient

from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AzureStoragePolicyService:
    def __init__(self, storage_mgmt_client: StorageManagementClient, state: dict = None) -> None:
        self.storage_mgmt_client = storage_mgmt_client
        self.state = state

    def create(self, account_name: str, days: int):
        if account_name is None:
            logger.info(f"Account Name: {self.state['azure']['resource_group_name']}")
        resource_group = self.state["azure"]["resource_group_name"]
        account_name = account_name or self.state["azure"]["storage_account_name"]
        s = self.storage_mgmt_client.management_policies.create_or_update(
            resource_group,
            account_name,
            "default",
            {
                "policy": {
                    "rules": [
                        {
                            "enabled": True,
                            "name": f"csm{days}days",
                            "type": "Lifecycle",
                            "definition": {
                                "filters": {"blob_types": ["blockBlob"]},
                                "actions": {
                                    "base_blob": {"delete": {"days_after_modification_greater_than": days}},
                                    "snapshot": {"delete": {"days_after_creation_greater_than": days}},
                                    "version": {"delete": {"days_after_creation_greater_than": days}},
                                },
                            },
                        }
                    ]
                }
            },
        )
        logger.info(f"Successfully created policy {s}")

    def delete(self, account_name: str):
        resource_group = self.state["azure"]["resource_group_name"]
        try:
            self.storage_mgmt_client.management_policies.delete(resource_group)
        except Exception as exp:
            logger.error(exp)
            return CommandResponse.fail()
        logger.info("Successfully deleted policy")
