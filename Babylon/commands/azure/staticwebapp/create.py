import logging
import pathlib

from click import Path
from click import option
from click import command
from click import argument
from typing import Any, Optional

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.staticwebapp.services.swa_api_svc import AzureSWAService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token()
@option(
    "--file",
    "swa_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path, exists=True),
    help="Your custom staticwebapp description file yaml",
)
@argument("webapp_name", type=str)
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    webapp_name: str,
    swa_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    service_state = state["services"]
    service = AzureSWAService(azure_token=azure_token, state=service_state)
    swa_file = swa_file or env.original_template_path / "webapp/webapp_details.yaml"
    github_secret = env.get_global_secret(resource="github", name="token")
    details = env.fill_template(
        data=swa_file.open().read(),
        state=state,
        ext_args={"github_secret": github_secret},
    )
    response = service.create(webapp_name=webapp_name, details=details)
    return CommandResponse.success(response, verbose=True)
