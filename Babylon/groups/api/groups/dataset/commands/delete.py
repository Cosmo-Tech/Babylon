from logging import getLogger
from click import argument
from click import option
from click import command
from click import confirm
from click import make_pass_decorator
from click import prompt
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import require_deployment_key
from Babylon.utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@pass_dataset_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
@argument("dataset_id", type=str, required=True)
def delete(
    dataset_api: DatasetApi,
    organization_id: str,
    dataset_id: str,
    dry_run: bool = False,
    force_validation: bool = False,
):
    """Unregister a dataset via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call dataset_api.delete_dataset")
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

        if not confirm(
            f"You are trying to delete dataset {dataset_id} datasets of organization {organization_id} \nDo you want to continue?"
        ):
            logger.info("Dataset deletion aborted.")
            return

        confirm_dataset_id = prompt("Confirm dataset id ")
        if confirm_dataset_id != dataset_id:
            logger.error("The dataset id you have type didn't mach with dataset you are trying to delete id")
            return
    else:
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
