import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.api import convert_keys_case
from ....utils.api import filter_api_response_item
from ....utils.api import underscore_to_camel
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **connector_api.find_connector_by_id**")
@timing_decorator
@pass_api_client
@option("-o",
        "--output_file",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        type=Path())
@argument("connector-id", type=QueryType())
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
def get(
    api_client: ApiClient,
    connector_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
) -> CommandResponse:
    """Get a registered connector details."""
    connector_api = ConnectorApi(api_client)
    try:
        retrieved_connector = connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_connector = filter_api_response_item(retrieved_connector, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_connector))
    if not output_file:
        logger.info(f"Connector {connector_id} details : ")
        logger.info(pformat(retrieved_connector))
        return CommandResponse.success(retrieved_connector)

    converted_connector_content = convert_keys_case(retrieved_connector, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_connector_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_connector_content, _f, ensure_ascii=False)
    logger.info(f"Connector {connector_id} data was dumped on {output_file}.")
    return CommandResponse.success(retrieved_connector)