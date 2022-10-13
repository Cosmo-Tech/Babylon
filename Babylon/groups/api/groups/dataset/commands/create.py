from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import timing_decorator
from ......utils.decorators import require_deployment_key
from ......utils.environment import Environment

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@timing_decorator
@pass_dataset_api
@pass_environment
@argument("dataset_file", type=str, required=False)
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("connector", "connector")
# @require_deployment_key("adt_url", "adt_url")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=str,
)
@option(
    "-n",
    "--name",
    "dataset_name",
    required=False,
    type=str,
    help="New dataset name",
)
@option(
    "-d",
    "--description",
    "dataset_description",
    required=False,
    type=str,
    help="New dataset description",
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="If true, the created Organization will be set as organization of current babylon context",
    required=False,
    default=True,
)
def create(
    env: Environment,
    dataset_api: DatasetApi,
    organization_id: str,
    dataset_file: str,
    select: bool,
    connector: str,
    # adt_url: str,
    dataset_name: str,
    dataset_description: Optional[str] = None,
    use_working_dir_file: bool = False,
    dry_run: bool = False,
):
    """Register new dataset by sending description file to the API."""

    if dry_run:
        logger.info("DRY RUN - Would call dataset_api.create_dataset")
        return

    if not dataset_file and not dataset_name:
        logger.error("Error : can not get an dataset name, please check your Dataset.YAML file or set --name option")
        return

    converted_dataset_content = get_api_file(
        api_file_path=dataset_file or f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Dataset.yaml",
        use_working_dir_file=use_working_dir_file if dataset_file else False,
        logger=logger,
    )

    if not converted_dataset_content:
        logger.error("Error : can not get Dataset definition, please check your Dataset.YAML file")
        return

    if not dataset_description and "dataset_description" not in converted_dataset_content:
        converted_dataset_content["description"] = dataset_name

    if "name" not in converted_dataset_content:
        converted_dataset_content["name"] = dataset_name

    if "connector" in converted_dataset_content:
        if "id" not in converted_dataset_content["connector"]:
            converted_dataset_content["connector"] = connector
    else:
        converted_dataset_content["connector"] = connector

    try:
        logger.info(pformat(converted_dataset_content))
        retrieved_dataset = dataset_api.create_dataset(
            organization_id=organization_id, dataset=converted_dataset_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} and / or Connector {connector['id']} does not exists.")
        return

    if select:
        env.configuration.set_deploy_var("dataset_id", retrieved_dataset["id"])
    logger.debug(pformat(retrieved_dataset))
    logger.info(f"Created new dataset with id: {retrieved_dataset['id']}")
