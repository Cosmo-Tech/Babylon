import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from click import option
from Babylon.commands.azure.staticwebapp.services.app_settings import (
    AzureSWASettingsAppService, )
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option(
    "--file",
    "settings_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom settings description file yaml",
)
@argument("webapp_name", type=QueryType())
@retrieve_state
def update(state: Any, azure_token: str, webapp_name: str, settings_file: pathlib.Path) -> CommandResponse:
    """
    Update static webapp app settings in the given webapp
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site-app-settings
    """
    service_state = state['services']
    service = AzureSWASettingsAppService(azure_token=azure_token, state=service_state)
    service.update(
        webapp_name=webapp_name,
        settings_file=settings_file,
    )
    return CommandResponse.success()
