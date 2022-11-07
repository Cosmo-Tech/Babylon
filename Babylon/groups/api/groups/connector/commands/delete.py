from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.interactive import confirm_deletion

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@describe_dry_run("Would call **connector_api.unregister_connector** and unregister a Connector")
@timing_decorator
@pass_connector_api
@argument(
    "connector_id",
    required=False,
)
@option(
    "-i",
    "--connector-file",
    "connector_file",
    help="In case the connector id is retrieved from a file",
)
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def delete(
    connector_api: ConnectorApi,
    connector_id: str,
    connector_file: Optional[str] = None,
    force_validation: bool = False,
    use_working_dir_file: bool = False,
):
    """Unregister a Connector via Cosmotech API."""

    if not connector_id:
        if not connector_file:
            logger.error("No id passed as argument or option use -i option"
                         " to pass an json or yaml file containing an connector id.")
            return

        converted_connector_content = get_api_file(
            api_file_path=connector_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_connector_content:
            logger.error("Can not get Connector definition, please check your file")
            return

        connector_id = converted_connector_content.get("id") or converted_connector_content.get("dataset_id")
        if not connector_id:
            logger.error(f"Could not found connector id in {connector_file}.")
            return

    try:
        connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} not found.")
        return

    if not force_validation and not confirm_deletion("Connector", connector_id):
        return

    logger.info(f"Deleting connector {connector_id}")

    try:
        connector_api.unregister_connector(connector_id)
        logger.info(f"Connector with id {connector_id} deleted.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the connector {connector_id}")
