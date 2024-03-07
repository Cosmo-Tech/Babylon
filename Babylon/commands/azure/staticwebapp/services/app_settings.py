import logging
import polling2

from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureSWASettingsAppService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token

    def get(self, webapp_name: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/listAppSettings?api-version=2022-03-01",
            self.azure_token,
            type="POST",
        )
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def update(self, webapp_name: str, details: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = polling2.poll(
            lambda: oauth_request(
                f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
                f"providers/Microsoft.Web/staticSites/{webapp_name}/config/appsettings?api-version=2022-03-01",
                self.azure_token,
                type="PUT",
                data=details,
            ),
            check_success=is_correct_response,
            step=1,
            timeout=60,
        )
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        logger.info("[webapp] app settings successfully updated")
        return output_data


def is_correct_response(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True
