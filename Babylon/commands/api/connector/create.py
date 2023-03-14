from logging import getLogger
from pprint import pformat
from typing import Optional
import pathlib

from click import Path
from click import Choice
from click import argument
from click import command
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.api import convert_keys_case
from ....utils.api import underscore_to_camel
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client
from ....utils.decorators import output_to_file
from ....utils.api import camel_to_underscore
from ....utils.environment import Environment

logger = getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATES = {
    "ADT": ".payload_templates/api/Connector.ADT.yaml",
    "STORAGE": ".payload_templates/api/Connector.STORAGE.yaml"
}


@command()
@describe_dry_run("Would call **connector_api.create_connector** to register a new Connector")
@timing_decorator
@pass_api_client
@argument("connector-name", type=QueryType())
@option("-t",
        "--type",
        "connector_type",
        required=True,
        type=Choice(["ADT", "STORAGE"], case_sensitive=False),
        help="Connector type, allowed values : [ADT, STORAGE]")
@option("-v", "--version", "connector_version", required=True, help="Version of the Connector")
@option("-i", "--connector-file", "connector_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@output_to_file
def create(api_client: ApiClient,
           connector_name: str,
           connector_type: str,
           connector_version: str,
           connector_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """Register a new Connector by sending a JSON or YAML file to the API."""
    connector_api = ConnectorApi(api_client)
    connector_type = connector_type.upper()
    connector_content = connector_file or DEFAULT_PAYLOAD_TEMPLATES[connector_type]
    env = Environment()
    converted_connector_content = convert_keys_case(
        env.fill_template(connector_content,
                          data={
                              "connector_name": connector_name,
                              "connector_version": connector_version,
                              "connector_key": connector_name.replace(" ", ""),
                              "connector_description": connector_name
                          }), camel_to_underscore)

    try:
        retrieved_connector = connector_api.register_connector(connector=converted_connector_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()

    converted_connector_content = convert_keys_case(retrieved_connector, underscore_to_camel)
    logger.debug(pformat(converted_connector_content))
    logger.info("Created new %s Connector with id: %s", connector_type, converted_connector_content['id'])

    return CommandResponse.success(converted_connector_content)
