import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator
from ......utils.decorators import require_deployment_key

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@allow_dry_run
@pass_dataset_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output_file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=str,
)
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    dataset_api: DatasetApi,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get all registered datasets."""

    if dry_run:
        logger.info("DRY RUN - Would call dataset_api.find_all_datasets")
        return

    try:
        retrieved_datasets = dataset_api.find_all_datasets(organization_id)
    except NotFoundException:
        logger.error(f"Organization {organization_id} was not found.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return

    if fields:
        retrieved_datasets = filter_api_response(retrieved_datasets, fields.split(","))
    logger.info(f"Found {len(retrieved_datasets)} datasets")
    if output_file:
        _datasets_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_datasets]
        try:
            with open(output_file, "w") as _file:
                json.dump(_datasets_to_dump, _file, ensure_ascii=False)
        except TypeError:
            with open(output_file, "w") as _file:
                json.dump([_ele.to_dict() for _ele in _datasets_to_dump], _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s.", output_file)
        return
    logger.info(pformat(retrieved_datasets, sort_dicts=False))
