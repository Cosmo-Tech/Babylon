from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from click import Path
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator
from ......utils.decorators import require_deployment_key

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@pass_dataset_api
@timing_decorator
@argument("dataset_file")
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("connector", "connector")
@require_deployment_key("dataset_id", "dataset_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def update(
    dataset_api: DatasetApi,
    dataset_file: str,
    connector: str,
    organization_id: str,
    dataset_id: str,
    dry_run: bool = False,
    use_working_dir_file: Optional[bool] = False,
):
    """Send a JSON or YAML file to the API to update a dataset."""

    if dry_run:
        logger.info("DRY RUN - Would call dataset_api.update_dataset")
        return

    converted_dataset_content = get_api_file(
        api_file_path=dataset_file,
        use_working_dir_file=use_working_dir_file,
        logger=logger,
    )

    if not converted_dataset_content:
        logger.error("Error : can not get Dataset definition, please check your Dataset file")
        return

    if "name" not in converted_dataset_content:
        logger.error("Error : can not get an dataset name, please check your Dataset file or set --name option")
        return

    converted_dataset_content["connector"] = connector

    try:
        retrieved_dataset = dataset_api.update_dataset(
            organization_id=organization_id,
            dataset_id=dataset_id,
            dataset=converted_dataset_content,
        )
    except NotFoundException:
        logger.error(f"Dataset {dataset_id} does not exists in organization {organization_id}.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")

    logger.debug(pformat(retrieved_dataset))
    logger.info(f"Updated dataset with id: {retrieved_dataset['id']}")
