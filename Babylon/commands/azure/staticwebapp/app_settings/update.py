import logging
import pathlib
import polling2

from typing import Any
from click import command
from click import argument
from click import Path
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_azure_token()
@option("--file", "settings_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_group_name', 'subscription_id'],
})
def update(context: Any, azure_token: str, webapp_name: str, settings_file: pathlib.Path) -> CommandResponse:
    """
    Update static webapp app settings in the given webapp
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site-app-settings
    """
    org_id = context['api_organization_id']
    work_key = context['api_workspace_key']
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    settings_file = settings_file or env.working_dir.original_template_path / "webapp/webapp_settings.json"
    secrets_powerbi = env.get_project_secret(organization_id=org_id, workspace_key=work_key, name="pbi")
    details = env.fill_template(settings_file, data={"secrets_powerbi": secrets_powerbi})
    response = polling2.poll(lambda: oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/config/appsettings?api-version=2022-03-01",
        azure_token,
        type="PUT",
        data=details),
                             check_success=is_correct_response,
                             step=1,
                             timeout=60)

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
