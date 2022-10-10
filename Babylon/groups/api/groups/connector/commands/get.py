import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from cosmotech_api.exceptions import NotFoundException, UnauthorizedException
from click import argument, command, make_pass_decorator, option
from cosmotech_api.api.connector_api import ConnectorApi

from Babylon.utils.api import convert_keys_case, underscore_to_camel, filter_api_response_item
from Babylon.utils.decorators import allow_dry_run, timing_decorator

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)

@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@option(
    "-o",
    "--output_file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=str,
)
@argument("connector_id", type=str)
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get(
    connector_api: ConnectorApi,
    connector_id,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get an registered connector data."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.find_connector_by_id")
        retrieved_connector = {"Babylon": "<DRY RUN>"}
        return

    try:
        retrieved_connector = connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException :
        logger.error("Unauthorized access to the cosmotech api")
    except NotFoundException :
        logger.error("Connector with id %s does not exists.", connector_id)
    if fields:
        retrieved_connector = filter_api_response_item(
            retrieved_connector, fields.split(",")
        )
    if not output_file :
        logger.info("Connector %s details : ", connector_id)
        logger.info(pformat(retrieved_connector))
    else:
        converted_content = convert_keys_case(
            retrieved_connector.to_dict(), underscore_to_camel
        )
        with open(output_file, "w") as _file:
            json.dump(converted_content, _file, ensure_ascii=False)
        logger.info("Connector %s data was dumped on %s.", connector_id, output_file )
