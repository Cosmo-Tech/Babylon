import logging
import pathlib
from typing import Optional

from click import Path
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

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("connector-name", type=QueryType())
@option("-i",
        "--connector-file",
        "connector_file",
        required=True,
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom connector description file (yaml or json)")
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new connector in configuration ?",
)
@output_to_file
def create(api_url: str,
           azure_token: str,
           connector_name: str,
           connector_file: Optional[pathlib.Path] = None,
           select: bool = False) -> CommandResponse:
    """
    Register a new Connector by sending a file to the API.
    See the API files to edit your own file manually
    """
    env = Environment()
    details = env.fill_template(connector_file,
                                data={
                                    "connector_name": connector_name,
                                    "connector_key": connector_name.replace(" ", "")
                                })
    if connector_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/connectors", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    logger.info(f"Created new connector with id: {connector['id']}")
    if select:
        value = "adt_connector_id"
        if env.configuration.get_deploy_var('adt_connector_id'):
            value = "storage_connector_id"
        logger.info(f"Updated configuration variables with {value}")
        env.configuration.set_deploy_var(value, connector["id"])
    return CommandResponse.success(connector, verbose=True)
