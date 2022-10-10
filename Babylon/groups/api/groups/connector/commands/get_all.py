import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command, make_pass_decorator, option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from Babylon.utils.api import convert_keys_case, filter_api_response, underscore_to_camel
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
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    connector_api: ConnectorApi,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get all registered connectors."""
    if dry_run:
        logger.info("DRY RUN - Would call connector_api.find_all_connectors")
        retrieved_connectors = [{"Babylon": "<DRY RUN>"}]
        return

    try:
        retrieved_connectors = connector_api.find_all_connectors()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
    if fields:
        retrieved_connectors = filter_api_response(
            retrieved_connectors, fields.split(",")
        )
    if not output_file:
        logger.info(pformat(retrieved_connectors))
        logger.info("Found %s connectors", len(retrieved_connectors))
    else:
        _connectors_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_connectors]
        with open(output_file, "w") as _file:
            json.dump(_connectors_to_dump, _file, ensure_ascii=False)
        logger.info("Found %s connectors", len(retrieved_connectors))
        logger.info("Full content was dumped on %s", output_file)