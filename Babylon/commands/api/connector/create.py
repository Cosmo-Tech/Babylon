import logging
from typing import Optional
import pathlib

from click import Path
from click import Choice
from click import argument
from click import command
from click import option

from ....utils.request import oauth_request
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.environment import Environment
from ....utils.decorators import require_platform_key
from ....utils.yaml_utils import yaml_to_json

logger = logging.getLogger("Babylon")

TEMPLATES = {"ADT": "api/connector.ADT.json", "STORAGE": "api/connector.STORAGE.json"}


@command()
@describe_dry_run("Would call **connector_api.create_connector** to register a new Connector")
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("connector-name", type=QueryType())
@option("-t",
        "--type",
        "connector_type",
        type=Choice(["ADT", "STORAGE"], case_sensitive=False),
        help="Connector type, allowed values : [ADT, STORAGE]")
@option("-v", "--version", "connector_version", required=True, help="Version of the Connector")
@option("-i",
        "--connector-file",
        "connector_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom connector description file (yaml or json)")
@output_to_file
def create(api_url: str,
           azure_token: str,
           connector_name: str,
           connector_type: str,
           connector_version: str,
           connector_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """
    Register a new Connector by sending a file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    if not connector_file and not connector_type:
        logger.error("Please specify a connector_file or choose a connector type to use default templates")
        return CommandResponse.fail()
    connector_file = connector_file or env.working_dir.payload_path / TEMPLATES[connector_type]
    details = env.fill_template(connector_file,
                                data={
                                    "connector_name": connector_name,
                                    "connector_version": connector_version,
                                    "connector_key": connector_name.replace(" ", ""),
                                    "connector_description": connector_name
                                })
    if connector_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/connectors", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    logger.info(f"Created new connector with id: {connector['id']}")
    return CommandResponse.success(connector, verbose=True)
