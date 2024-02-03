import logging
import polling2

from pathlib import Path
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse


logger = logging.getLogger("Babylon")
env = Environment()


class AzureSWASettingsAppService:

    def get(self, context: dict, webapp_name: str, azure_token: str):
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        response = oauth_request(
            f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
            f"providers/Microsoft.Web/staticSites/{webapp_name}/listAppSettings?api-version=2022-03-01",
            azure_token,
            type="POST",
        )
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def update(
        self, webapp_name: str, context: dict, settings_file: Path, azure_token: str
    ):
        org_id = context["api_organization_id"]
        work_key = context["api_workspace_key"]
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        settings_file = (
            settings_file
            or env.working_dir.original_template_path / "webapp/webapp_settings.json"
        )
        secrets_powerbi = env.get_project_secret(
            organization_id=org_id, workspace_key=work_key, name="pbi"
        )
        details = env.fill_template(
            settings_file, data={"secrets_powerbi": secrets_powerbi}
        )
        response = polling2.poll(
            lambda: oauth_request(
                f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
                f"providers/Microsoft.Web/staticSites/{webapp_name}/config/appsettings?api-version=2022-03-01",
                azure_token,
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
        logger.info("Successfully updated")
        return CommandResponse.success(output_data, verbose=True)


def is_correct_response(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True
