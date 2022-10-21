import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
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
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=bool,
)
@option(
    "-n",
    "--name",
    "dataset_name",
    type=str,
    help="New dataset name",
)
@option(
    "-d",
    "--description",
    "dataset_description",
    type=str,
    help="New dataset description",
)
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="If true, the created Organization will be set as organization of current babylon context",
    default=True,
)
def create(
    env: Environment,
    dataset_api: DatasetApi,
    organization_id: str,
    select: bool,
    connector: str,
    output_file: Optional[str] = None,
    dataset_file: Optional[str] = None,
    dataset_name: Optional[str] = None,
    dataset_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
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

    converted_dataset_content["connector"] = connector

    try:
        retrieved_dataset = dataset_api.create_dataset(organization_id=organization_id,
                                                       dataset=converted_dataset_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} and / or Connector {connector['id']} does not exists.")
        return

    if select:
        env.configuration.set_deploy_var("dataset_id", retrieved_dataset["id"])

    logger.info(f"Created new dataset with id: {retrieved_dataset['id']}")
    logger.debug(pformat(retrieved_dataset))

    if output_file:
        converted_content = convert_keys_case(retrieved_dataset, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")
