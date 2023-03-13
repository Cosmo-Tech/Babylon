from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.api import convert_keys_case
from ....utils.api import filter_api_response
from ....utils.api import underscore_to_camel
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **connector_api.find_all_connectors** and retrieve all registered Connectors")
@timing_decorator
@pass_api_client
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
@output_to_file
def get_all(api_client: ApiClient, fields: Optional[str] = None) -> CommandResponse:
    """Get all registered connectors."""
    connector_api = ConnectorApi(api_client)
    try:
        retrieved_connectors = connector_api.find_all_connectors()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()

    if fields:
        retrieved_connectors = filter_api_response(retrieved_connectors, fields.replace(" ", "").split(","))
    logger.info(f"Found {len(retrieved_connectors)} connectors")
    logger.debug(pformat(retrieved_connectors))

    _connectors_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_connectors]
    try:
        data = [_ele.to_dict() for _ele in _connectors_to_dump]
    except AttributeError:
        data = _connectors_to_dump
    return CommandResponse.success({"connectors": data})
