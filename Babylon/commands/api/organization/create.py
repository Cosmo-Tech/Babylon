import pathlib
from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option

from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("organization_file", type=pathlib.Path)
@option("--organization-name", "organization_name", type=QueryType(), help="Your custom organization name")
@option(
    "--no-select",
    "no_select",
    is_flag=True,
    help="Don't select this new organization in configuration ?",
)
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    organization_file: pathlib.Path,
    organization_name: Optional[str] = None,
    no_select: bool = False,
) -> CommandResponse:
    """
    Register new dataset by sending description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    # organization_file = organization_file or env.working_dir.payload_path / "api/organization.json"
    details = env.fill_template(organization_file, data={"organization_name": organization_name})
    if organization_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(f"Successfully created organization {organization['id']}")
    select = not no_select
    if select:
        logger.info("Updated configuration variables with organization_id")
        env.configuration.set_deploy_var("organization_id", organization["id"])
    return CommandResponse.success(organization, verbose=True)
