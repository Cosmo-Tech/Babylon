import json
from logging import getLogger
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from rich import print
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.find_all_datasets**")
@pass_dataset_api
@timing_decorator
@require_deployment_key("organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(writable=True),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_all(dataset_api: DatasetApi,
            organization_id: str,
            output_file: Optional[str] = None,
            fields: Optional[str] = None):
    """Get all registered datasets."""
    try:
        retrieved_datasets = dataset_api.find_all_datasets(organization_id)
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if fields:
        retrieved_datasets = filter_api_response(retrieved_datasets, fields.replace(" ", "").split(","))
    logger.info(f"Found {len(retrieved_datasets)} datasets")
    if not output_file:
        print(retrieved_datasets)
        return

    _datasets_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_datasets]
    with open(output_file, "w") as _file:
        try:
            json.dump([_ele.to_dict() for _ele in _datasets_to_dump], _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_datasets_to_dump, _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s.", output_file)
