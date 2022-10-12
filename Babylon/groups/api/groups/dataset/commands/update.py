from logging import getLogger
from pprint import pformat

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from Babylon.utils.api import get_api_file
from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import require_deployment_key
from Babylon.utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@pass_dataset_api
@timing_decorator
@argument("dataset_file", type=str)
@require_deployment_key("organization_id", "organization_id")
@option(
    "-d",
    "--dataset",
    "dataset_id",
    help="Dataset id",
    required=True,
    type=str,
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=str,
)
def update(
    dataset_api: DatasetApi,
    dataset_file: str,
    organization_id: str,
    dataset_id: str,
    dry_run: bool = False,
    use_working_dir_file: bool = False,
):
    """Send a JSON or YAML file to the API to update a dataset."""

    if (
        converted_dataset_content := get_api_file(
            api_file_path=dataset_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
    ) is not None:
        try:

            if not dry_run:
                retrieved_dataset = dataset_api.update_dataset(
                    organization_id=organization_id,
                    dataset_id=dataset_id,
                    dataset=converted_dataset_content,
                )
            else:
                logger.info("DRY RUN - Would call dataset_api.update_dataset")
                retrieved_dataset = converted_dataset_content
                retrieved_dataset["id"] = dataset_id
            logger.debug(pformat(retrieved_dataset))
            logger.info(f"Updated dataset with id: {retrieved_dataset['id']}")
        except NotFoundException:
            logger.error(f"Dataset {dataset_id} does not exists in organization {organization_id}.")
        except UnauthorizedException:
            logger.error("Unauthorized access to the cosmotech api")
    else:
        logger.error("Error : can not get correct connector definition, please check your Dataset.YAML file")
