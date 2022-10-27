import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@option("-o",
        "--output_file",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        type=Path())
@argument("connector-id")
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
def get(
    connector_api: ConnectorApi,
    connector_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
    dry_run: Optional[bool] = False,
):
    """Get a registered connector details."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.find_connector_by_id")
        return

    try:
        retrieved_connector = connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} does not exists.")
        return

    if fields:
        retrieved_connector = filter_api_response_item(retrieved_connector, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_connector))
    if not output_file:
        logger.info(f"Connector {connector_id} details : ")
        logger.info(pformat(retrieved_connector))
        return

    converted_connector_content = convert_keys_case(retrieved_connector, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_connector_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_connector_content, _f, ensure_ascii=False)
    logger.info(f"Connector {connector_id} data was dumped on {output_file}.")
