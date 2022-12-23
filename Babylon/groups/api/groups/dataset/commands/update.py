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
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

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
@describe_dry_run("Would call **dataset_api.update_dataset**")
@pass_dataset_api
@timing_decorator
@argument("dataset-id", type=QueryType())
@require_deployment_key("organization_id", "organization_id")
@option("-c", "--connector-id", "connector_id", type=QueryType())
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
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
def update(
    dataset_api: DatasetApi,
    dataset_file: str,
    organization_id: str,
    dataset_id: str,
    connector_id: Optional[str] = None,
    output_file: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Send a JSON or YAML file to the API to update a dataset."""

    converted_dataset_content = get_api_file(
        api_file_path=dataset_file,
        use_working_dir_file=use_working_dir_file
    )

    if not converted_dataset_content:
        logger.error("Error : can not get Dataset definition, please check your Dataset file")
        return CommandResponse.fail()

    if "name" not in converted_dataset_content:
        logger.error("Error : can not get an dataset name, please check your Dataset file")
        return CommandResponse.fail()

    if converted_dataset_content.get("id"):
        del converted_dataset_content["id"]

    if connector_id:
        converted_dataset_content["connector"]["id"] = connector_id

    try:
        retrieved_dataset = dataset_api.update_dataset(
            organization_id=organization_id,
            dataset_id=dataset_id,
            dataset=converted_dataset_content,
        )
    except NotFoundException:
        logger.error(f"Dataset {dataset_id} not found in organization {organization_id}.")
        return CommandResponse.fail()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} and or Connector {connector_id} not found.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to update the dataset : {dataset_id}")
        return CommandResponse.fail()

    if output_file:
        converted_content = convert_keys_case(retrieved_dataset, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")

    logger.debug(pformat(retrieved_dataset))
    logger.info(f"Updated dataset with id: {retrieved_dataset['id']}")
    return CommandResponse(data=retrieved_dataset)
