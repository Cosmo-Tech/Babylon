from logging import getLogger

from click import argument, command, confirm, make_pass_decorator, prompt
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import NotFoundException, UnauthorizedException

from Babylon.utils.decorators import allow_dry_run, timing_decorator

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@argument("connector_id", type=str)
def delete(
    connector_api: ConnectorApi,
    connector_id: str,
    dry_run: bool = False,
):
    """Unregister a connector via Cosmotech API."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.unregister_connector")
        return

    try:
        _ = connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except NotFoundException:
        logger.error("Connector with id %s does not exists.", connector_id)
        return

    if not confirm(
        f"You are trying to delete connector {connector_id} \nDo you want to continue ?"
    ):
        logger.info("Connector deletion aborted.")
        return

    confirm_connector_id = prompt("Confirm connector id ")

    if confirm_connector_id != connector_id:
        logger.error("Wrong Connector , the id must be the same as the one that has been provide in delete command argument")
        return

    try:
        _ = connector_api.unregister_connector(connector_id)
        logger.info("Connector with id %s deleted.",connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
