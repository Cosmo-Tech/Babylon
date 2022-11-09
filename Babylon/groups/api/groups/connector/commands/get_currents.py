import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
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
        help="The path to the file where Connectors should be outputted (json-formatted)",
        type=Path())
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
@require_deployment_key("adt_connector_id", "adt_connector_id")
@require_deployment_key("storage_connector_id", "storage_connector_id")
def get_currents(
    connector_api: ConnectorApi,
    adt_connector_id: str,
    storage_connector_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
    dry_run: Optional[bool] = False,
):
    """Get a registered connector details."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.find_connector_by_id")
        return

    try:
        retrieved_adt_connector = connector_api.find_connector_by_id(adt_connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Connector with id {adt_connector_id} not found.")
        return

    try:
        retrieved_storage_connector = connector_api.find_connector_by_id(storage_connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Connector with id {storage_connector_id} not found.")
        return

    retrieved_connectors = [retrieved_adt_connector, retrieved_storage_connector]
    logger.info("Retrieving current platform Connectors ...")
    logger.debug(pformat(retrieved_connectors))
    if fields:
        retrieved_connectors = filter_api_response(retrieved_connectors, fields.replace(" ", "").split(","))
    if not output_file:
        logger.info(pformat(retrieved_connectors))
        return

    _connectors_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_connectors]
    with open(output_file, "w") as _file:
        try:
            json.dump([_ele.to_dict() for _ele in _connectors_to_dump], _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_connectors_to_dump, _file, ensure_ascii=False)
    logger.info(f"Full content was dumped on {output_file}")
