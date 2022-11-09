from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.update_dataset**")
@pass_dataset_api
@timing_decorator
@argument("dataset_file")
@require_deployment_key("organization_id", "organization_id")
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
    use_working_dir_file: Optional[bool] = False,
):
    """Send a JSON or YAML file to the API to update a dataset."""

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
        logger.error(f"Dataset {dataset_id} not found in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} and or Connector {connector['id']} not found.")
        return
    except ForbiddenException:
        logger.error(f"You are not allowed to update the dataset : {dataset_id}")
        return

    logger.debug(pformat(retrieved_dataset))
    logger.info(f"Updated dataset with id: {retrieved_dataset['id']}")
