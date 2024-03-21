import logging
from pathlib import Path
from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureSWACustomDomainService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token

    def upsert(
        self,
        webapp_name: str,
        domain_name: str,
        create_file: Path,
    ):
        check_ascii(webapp_name)
        check_ascii(domain_name)
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        if not domain_name:
            return CommandResponse.fail()
        create_route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01")
        details = '{"properties":{}}'
        if create_file:
            details = env.fill_template(data=create_file.open().read(), state=self.state)
        response = oauth_request(create_route, self.azure_token, type="PUT", data=details)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        logger.info("Successfully launched")
        return output_data

    def get_all(self, webapp_name: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains?api-version=2022-03-01",
            self.azure_token,
            type="GET")
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        return output_data

    def get(self, webapp_name: str, domain_name: str):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01",
            self.azure_token,
            type="GET")
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def delete(
        self,
        webapp_name: str,
        domain_name: str,
        force_validation: bool,
    ):
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        if not force_validation and not confirm_deletion("domain", domain_name):
            return CommandResponse.fail()
        logger.info(f"Deleting custom domain {domain_name} for static webapp {webapp_name}")
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01",
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            return CommandResponse.fail()
        logger.info("Successfully launched")
