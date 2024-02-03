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

    def upsert(
        self,
        webapp_name: str,
        domain_name: str,
        context: dict,
        create_file: Path,
        azure_token: str,
    ):
        check_ascii(webapp_name)
        check_ascii(domain_name)
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        if not domain_name:
            return CommandResponse.fail()
        create_route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01"
        )
        details = '{"properties":{}}'
        if create_file:
            details = env.fill_template(create_file)
        response = oauth_request(create_route, azure_token, type="PUT", data=details)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        logger.info("Successfully launched")
        return output_data

    def get_all(self, webapp_name: str, context: dict, azure_token: str):
        azure_subscription = context['azure_subscription_id']
        resource_group_name = context['azure_resource_group_name']
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains?api-version=2022-03-01",
            azure_token,
            type="GET")
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        return output_data

    def get(self, webapp_name: str, domain_name: str, context: dict, azure_token: str):
        azure_subscription = context['azure_subscription_id']
        resource_group_name = context['azure_resource_group_name']
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01",
            azure_token,
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
        context: dict,
        azure_token: str,
    ):
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        if not force_validation and not confirm_deletion("domain", domain_name):
            return CommandResponse.fail()
        logger.info(
            f"Deleting custom domain {domain_name} for static webapp {webapp_name}"
        )
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01",
            azure_token,
            type="DELETE",
        )
        if response is None:
            return CommandResponse.fail()
        logger.info("Successfully launched")
