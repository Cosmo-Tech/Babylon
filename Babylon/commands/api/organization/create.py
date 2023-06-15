from logging import getLogger
from typing import Optional
import pathlib

from click import argument
from click import command
from click import option
from click import Path

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("organization-name", type=QueryType())
@option("-e","--email", "security_id", type=QueryType())
@option("-s","--security-role", "security_role", type=QueryType(), default="Admin")
@option("-i",
        "--organization-file",
        "organization_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom organization description file (yaml or json)")
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new organization in configuration ?",
)
@output_to_file
def create(api_url: str,
           azure_token: str,
           organization_name: str,
           security_id: str,
           security_role: str,
           organization_file: Optional[pathlib.Path] = None,
           select: bool = False) -> CommandResponse:
    """
    Register new dataset by sending description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    organization_file = organization_file or env.working_dir.payload_path / "api/organization.yaml"
    details = env.fill_template(organization_file, data={
        "organization_name": organization_name,
        "security_id": security_id,
        "security_role": security_role
    })
    if organization_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(f"Successfully created organization {organization['id']}")
    if select:
        logger.info("Updated configuration variables with organization_id")
        env.configuration.set_deploy_var("organization_id", organization["id"])
    return CommandResponse.success(organization, verbose=True)
