import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@describe_dry_run("Would call **connector_api.find_all_connectors** and retrieve all registered Connectors")
@timing_decorator
@pass_connector_api
@option("-o",
        "--output_file",
        "output_file",
        help="The path to the file where Connectors should be outputted (json-formatted)",
        type=Path())
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
def get_all(
    connector_api: ConnectorApi,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
) -> CommandResponse:
    """Get all registered connectors."""

    try:
        retrieved_connectors = connector_api.find_all_connectors()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()

    if fields:
        retrieved_connectors = filter_api_response(retrieved_connectors, fields.replace(" ", "").split(","))
    logger.info(f"Found {len(retrieved_connectors)} connectors")
    logger.debug(pformat(retrieved_connectors))
    if not output_file:
        logger.info(pformat(retrieved_connectors))
        return CommandResponse.success({"connectors": retrieved_connectors})

    _connectors_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_connectors]
    with open(output_file, "w") as _file:
        try:
            json.dump([_ele.to_dict() for _ele in _connectors_to_dump], _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_connectors_to_dump, _file, ensure_ascii=False)
    logger.info(f"Full content was dumped on {output_file}")
    return CommandResponse.success({"connectors": retrieved_connectors})
