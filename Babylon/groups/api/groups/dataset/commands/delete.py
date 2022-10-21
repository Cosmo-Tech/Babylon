from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@pass_dataset_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
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
    type=bool,
)
@option(
    "-d",
    "--dataset-file",
    "dataset_file",
    help="In case the dataset id is retrieved from a file",
    required=False,
)
@argument("dataset_id", type=str, required=False)
def delete(
    dataset_api: DatasetApi,
    organization_id: str,
    dataset_file: Optional[str] = None,
    dataset_id: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
    dry_run: Optional[bool] = False,
    force_validation: Optional[bool] = False,
):
    """Unregister a dataset via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call dataset_api.delete_dataset")
        return

    if not dataset_id:
        if not dataset_file:
            logger.error("No id passed as argument or option use -d option"
                         " to pass an json or yaml file containing an dataset id.")
            return

        converted_dataset_content = get_api_file(
            api_file_path=dataset_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_dataset_content:
            logger.error("Error : can not get Dataset definition, please check your file")
            return

        if converted_dataset_content["id"]:
            dataset_id = converted_dataset_content["id"]
        elif converted_dataset_content["dataset_id"]:
            dataset_id = converted_dataset_content["dataset_id"]
        else:
            logger.error(f"Could not found dataset id in {dataset_file}.")
            return

    try:
        dataset_api.find_dataset_by_id(dataset_id=dataset_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Dataset {dataset_id} does not exists in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if not force_validation:

        if not confirm(f"You are trying to delete dataset {dataset_id} datasets of organization {organization_id} \n"
                       "Do you want to continue?"):
            logger.info("Dataset deletion aborted.")
            return

        confirm_dataset_id = prompt("Confirm dataset id ")
        if confirm_dataset_id != dataset_id:
            logger.error("The dataset id you have type didn't mach with dataset you are trying to delete id")
            return

    logger.info(f"Deleting dataset {dataset_id}")

    try:
        dataset_api.delete_dataset(organization_id=organization_id, dataset_id=dataset_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return
    logger.info(f"Datasets {dataset_id} of organization {organization_id} deleted.")
