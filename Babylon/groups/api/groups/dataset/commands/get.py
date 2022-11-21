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

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.typing import QueryType

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.find_dataset_by_id**")
@pass_dataset_api
@timing_decorator
@argument("dataset_id", type=QueryType())
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
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
    "--from-file",
    "from_file",
    is_flag=True,
    help="In case the dataset id is retrieved from a file",
)
def get(
    dataset_api: DatasetApi,
    dataset_id: str,
    organization_id: str,
    output_file: Optional[str] = None,
    from_file: bool = False,
    use_working_dir_file: Optional[bool] = False,
    fields: str = None,
):
    """Get the state of the dataset in the API."""

    if from_file:
        dataset_file = dataset_id
        converted_dataset_content = get_api_file(
            api_file_path=dataset_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if converted_dataset_content["id"]:
            dataset_id = converted_dataset_content["id"]
        elif converted_dataset_content["dataset_id"]:
            dataset_id = converted_dataset_content["dataset_id"]
        else:
            logger.error(f"Could not found dataset id in {dataset_file}.")
            return

    try:
        retrieved_dataset = dataset_api.find_dataset_by_id(dataset_id=dataset_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Dataset {dataset_id} does not  in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if fields:
        retrieved_dataset = filter_api_response_item(retrieved_dataset, fields.replace(" ", "").split(","))
    if not output_file:
        logger.info(f"Dataset {dataset_id} details :")
        logger.info(pformat(retrieved_dataset))
        return

    converted_content = convert_keys_case(retrieved_dataset, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content, _f, ensure_ascii=False)
        except TypeError:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
    logger.info(f"Datset {dataset_id} detail was dumped on {output_file}")
    logger.debug(pformat(retrieved_dataset))
