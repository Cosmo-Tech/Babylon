from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option
from rich.pretty import pprint

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("organization-name", type=QueryType())
@option(
    "-i",
    "--organization-file",
    "organization_file",
    type=str,
    help="Your custom organization description file",
)
@output_to_file
def create(api_url: str,
           azure_token: str,
           organization_name: str,
           organization_file: Optional[str] = None) -> CommandResponse:
    """Register new dataset by sending description file to the API."""
    env = Environment()
    organization_file = organization_file or env.working_dir.payload_path / "api/organization.json"
    details = env.fill_template(organization_file, data={"organization_name": organization_name})
    response = oauth_request(f"{api_url}/organizations", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    pprint(organization)
    logger.info(f"Successfully created organization {organization['id']}")
    return CommandResponse.success(organization)
