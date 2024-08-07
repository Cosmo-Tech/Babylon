import jmespath
import logging
import polling2

from pathlib import Path

from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
# from Babylon.utils.interactive import confirm_deletion
# from azure.mgmt.resource import ResourceManagementClient
# from Babylon.utils.credentials import get_azure_credentials

logger = logging.getLogger("Babylon")
env = Environment()


class AzureSWAService:

    def __init__(
        self,
        azure_token: str,
        state: dict = None,
    ) -> None:
        self.state = state
        self.azure_token = azure_token

    def create(self, webapp_name: str, details: str):
        check_ascii(webapp_name)
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
        response = oauth_request(route, self.azure_token, type="PUT", data=details)
        if response is None:
            logger.error(f"[webapp] Failed to create webapp {webapp_name} in resource group {resource_group_name}")
            return None
        output_data = response.json()
        logger.info(f"[webapp] successfully launched of webapp {webapp_name} in resource group {resource_group_name}")
        return output_data

    def delete(self, webapp_name: str, force_validation: bool):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        if not force_validation and not confirm_deletion("webapp", webapp_name):
            return CommandResponse.fail()
        logger.info(f"[webapp] deleting static webapp {webapp_name} from resource group {resource_group_name}")

        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
        response = oauth_request(route, self.azure_token, type="DELETE")
        if response is None:
            logger.error(
                f"[webapp] Failed to delete of static webapp {webapp_name} from resource group {resource_group_name}")
            return CommandResponse.fail()
        logger.info(
            f"Successfully launched deletion of static webapp {webapp_name} from resource group {resource_group_name}")
        response_polling = polling2.poll(
            lambda: oauth_request(
                f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
                f"/providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01",
                self.azure_token,
            ),
            check_success=is_webapp_deleted,
            step=1,
            timeout=60,
        )
        if response_polling is None:
            logger.error(f"[webapp] Failed to delete static webapp {webapp_name}")
            return CommandResponse.fail(verbose=False)

    def get_all(self, filter: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
            "/providers/Microsoft.Web/staticSites?api-version=2022-03-01",
            self.azure_token,
        )
        if response is None:
            logger.error(f"[webapp] Failed to get all subscriptions in resource groups {resource_group_name}")
            return None
        output_data = response.json().get("value")
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get(self, webapp_name: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = polling2.poll(
            lambda: oauth_request(
                f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
                f"/providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01",
                self.azure_token,
            ),
            check_success=is_correct_response,
            step=1,
            timeout=60,
        )
        if response is None:
            logger.error(f"[webapp] Failed to get static webapp {webapp_name}")
            return None
        outputdata = response.json()
        return outputdata

    def update(self, webapp_name: str, swa_file: Path):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        swa_file = (swa_file or env.original_template_path / "webapp/webapp_details.yaml")
        github_secret = env.get_global_secret(resource="github", name="token")
        details = env.fill_template(data=swa_file.open().read(),
                                    state=self.state,
                                    ext_args={"github_secret": github_secret})
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
        response = oauth_request(route, self.azure_token, type="PUT", data=details)
        if response is None:
            logger.error(f"[webapp] Failed to update static webapp {webapp_name}")
            return None
        output_data = response.json()
        logger.info("[webapp] update successfully launched")
        return output_data


def is_correct_response(response):
    if response is None:
        return " "
    output_data = response.json()
    if "id" in output_data:
        return output_data


def is_webapp_deleted(response):
    if response is None:
        return None
    return True
