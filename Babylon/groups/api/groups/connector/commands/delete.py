from logging import getLogger

from click import argument, command, confirm, make_pass_decorator, prompt
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import NotFoundException, UnauthorizedException

from ......utils.decorators import allow_dry_run, timing_decorator

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
    """Unregister a connector via Cosmotech APi."""

    if confirm(
        f"You are trying to delete connector {connector_id} \nDo you want to continue ?"
    ):
        confirm_connector_id = connector_id
        try:
            if confirm_connector_id == connector_id:
                if dry_run:

                    logger.info(
                        "DRY RUN - Would call connector_api.unregister_connector"
                    )
                else:
                    _ = connector_api.unregister_connector(connector_id)
                    logger.info(f"Connector with id {connector_id} deleted.")
            else:
                logger.error(
                    "The connector id you have type don't mach with connector with id {connector_id} name"
                )
        except UnauthorizedException:
            logger.error("Unauthorized access to the cosmotech api")
        except NotFoundException:
            logger.error(f"Connector with id {connector_id} does not exists.")
    else:
        logger.info("Connector deletion aborted.")
