import logging
from pathlib import Path

import jmespath
from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureAppInsightService:

    def create(self, name: str, context: dict, file: Path, azure_token: str):
        check_ascii(name)
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        create_file = (
            file or env.working_dir.original_template_path / "webapp/app_insight.json"
        )
        details = env.fill_template(create_file)
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Insights/components/{name}?api-version=2015-05-01"
        )

        response = oauth_request(route, azure_token, type="PUT", data=details)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        logger.info("Successfully launched")
        return output_data

    def delete(
        self, name: str, context: dict, force_validation: bool, azure_token: str
    ):
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        if not force_validation and not confirm_deletion("appinsight", name):
            return CommandResponse.fail()
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Insights/components/{name}?api-version=2015-05-01"
        )
        response = oauth_request(route, azure_token, type="DELETE")
        if response is None:
            return CommandResponse.fail()
        if response.status_code == 204:
            logger.warn("App Insight not found")
            return CommandResponse.fail()
        logger.info("Successfully deleted")

    def get_all(self, context: dict, azure_token: str):
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Insights/components?api-version=2015-05-01"
        )
        response = oauth_request(route, azure_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()["value"]
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get(self, name: str, context: dict, azure_token: str):
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        route = (
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Insights/components/{name}?api-version=2015-05-01"
        )
        response = oauth_request(route, azure_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data