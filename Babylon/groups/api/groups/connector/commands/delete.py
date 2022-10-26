from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
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
    dry_run: Optional[bool] = False,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
):
    """Unregister a Connector via Cosmotech API."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.unregister_connector qnd unregister a Connector")
        return

    if not connector_id:
        if not connector_file:
            logger.error("No id passed as argument or option use -d option"
                         " to pass an json or yaml file containing an connector id.")
            return

        converted_connector_content = get_api_file(
            api_file_path=connector_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_connector_content:
            logger.error("Can not get Workspace definition, please check your file")
            return

        if "id" not in converted_connector_content and "dataset_id" not in converted_connector_content:
            logger.error(f"Could not found connector id in {connector_file}.")
            return

        try:
            connector_id = converted_connector_content["id"]
        except KeyError:
            connector_id = converted_connector_content["dataset_id"]

    try:
        connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} does not exists.")
        return

    if not force_validation:
        if not confirm(f"You are trying to delete connector {connector_id} \nDo you want to continue ?"):
            logger.info("Connector deletion aborted.")
            return

        confirm_connector_id = prompt("Confirm connector id ")
        if confirm_connector_id != connector_id:
            logger.error("Wrong Connector id, "
                         "the id must be the same as the one that has been provide in delete command argument")
            return

    logger.info(f"Deleting connector {connector_id}")

    try:
        connector_api.unregister_connector(connector_id)
        logger.info(f"Connector with id {connector_id} deleted.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the connector {connector_id}")
