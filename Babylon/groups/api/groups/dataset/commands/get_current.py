import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.find_dataset_by_id**")
@pass_dataset_api
@timing_decorator
@require_deployment_key("dataset_id")
@require_deployment_key("organization_id")
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
def get_current(
    dataset_api: DatasetApi,
    dataset_id: str,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: str = None,
):
    """Get the state of the dataset in the API."""
    try:
        retrieved_dataset = dataset_api.find_dataset_by_id(dataset_id=dataset_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Dataset {dataset_id} not found in organization {organization_id}.")
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
