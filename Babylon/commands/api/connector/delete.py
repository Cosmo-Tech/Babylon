from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.typing import QueryType
from ....utils.interactive import confirm_deletion
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **connector_api.unregister_connector** and unregister a Connector")
@timing_decorator
@pass_api_client
@argument(
    "connector_id",
    type=QueryType(),
)
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(api_client: ApiClient, connector_id: str, force_validation: Optional[bool] = False) -> CommandResponse:
    """Unregister a Connector via Cosmotech API."""
    connector_api = ConnectorApi(api_client)
    try:
        connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} not found.")
        return CommandResponse.fail()

    if not force_validation and not confirm_deletion("connector", connector_id):
        return CommandResponse.fail()

    logger.info(f"Deleting connector {connector_id}")

    try:
        connector_api.unregister_connector(connector_id)
        logger.info(f"Connector with id {connector_id} deleted.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the connector {connector_id}")
        return CommandResponse.fail()
    return CommandResponse.success()
