import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command, make_pass_decorator, option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case, filter_api_response, underscore_to_camel
from ......utils.decorators import allow_dry_run, timing_decorator

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
    """Get all registered connector."""
    try:
        if dry_run:
            logger.info("DRY RUN - Would call connector_api.find_all_connectors")
            retrieved_connectors = [{"Babylon": "<DRY RUN>"}]
        else:
            retrieved_connectors = connector_api.find_all_connectors()
            if fields is not None:
                retrieved_connectors = filter_api_response(
                    retrieved_connectors, fields.split(",")
                )
        if output_file is not None:
            _connectors_to_dump = []
            for _ele in retrieved_connectors:
                converted_content = convert_keys_case(
                    _ele.to_dict(), underscore_to_camel
                )
                _connectors_to_dump.append(converted_content)
            with open(output_file, "w") as _file:
                json.dump(_connectors_to_dump, _file, ensure_ascii=False)
            logger.info(f"{len(_connectors_to_dump)} Connectors found")
            logger.info(f"Full content was dumped on {output_file}")
        else:
            logger.info(pformat(retrieved_connectors))
            logger.info(f"Found {len(retrieved_connectors)} connectors")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
