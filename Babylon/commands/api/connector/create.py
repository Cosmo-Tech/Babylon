import logging
import pathlib
from typing import Optional

from click import argument
from click import command
from click import option
from click import Path

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
@argument("connector_file",
          type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@option("--connector-name", "connector_name", type=QueryType())
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    connector_file: pathlib.Path,
    connector_name: Optional[str] = None,
) -> CommandResponse:
    """
    Register a new Connector by sending a file to the API.
    See the API files to edit your own file manually
    """
    env = Environment()
    # Extract the connector key from the connector name if name is provided
    connector_key = connector_name.replace(" ", "") if connector_name else None
    # Fill the template with the connector name and key if maco variables are present in the connector file
    # ex: {{connector_name}}
    details = env.fill_template(connector_file,
                                data={
                                    "connector_name": connector_name,
                                    "connector_key": connector_key,
                                })
    if connector_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/connectors", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    logger.info(f"Created new connector with id: {connector['id']}")
    return CommandResponse.success(connector, verbose=True)
