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
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.typing import QueryType
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.create_dataset**")
@timing_decorator
@pass_dataset_api
@argument("dataset-name", required=False, type=QueryType())
@option("-c", "--connector-id", "connector_id", type=QueryType())
@require_deployment_key("organization_id", "organization_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=bool,
)
@option(
    "-i",
    "--dataset-file",
    "dataset_file",
    type=str,
    help="Your custom dataset description file",
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
def create(
    dataset_api: DatasetApi,
    organization_id: str,
    dataset_name: str,
    connector_id: Optional[str] = None,
    output_file: Optional[str] = None,
    dataset_file: Optional[str] = None,
    dataset_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Register new dataset by sending description file to the API."""

    converted_dataset_content = get_api_file(api_file_path=dataset_file or
                                             f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Dataset.yaml",
                                             use_working_dir_file=use_working_dir_file if dataset_file else False)

    if not converted_dataset_content:
        logger.error("Error : can not get Dataset definition, please check your Dataset.YAML file")
        return CommandResponse.fail()

    if not dataset_description and "dataset_description" not in converted_dataset_content:
        converted_dataset_content["description"] = dataset_name

    converted_dataset_content["name"] = dataset_name
    converted_dataset_content["connector"]["id"] = connector_id

    try:
        retrieved_dataset = dataset_api.create_dataset(organization_id=organization_id,
                                                       dataset=converted_dataset_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} and or Connector {connector_id} not found.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} and or Connector {connector_id} not found.")
        return CommandResponse.fail()

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

    return CommandResponse.success(retrieved_dataset)
