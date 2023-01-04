import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run, require_deployment_key, timing_decorator
from ......utils.typing import QueryType
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_dataset_api = make_pass_decorator(DatasetApi)


@command()
@describe_dry_run("Would call **dataset_api.search_datasets**")
@pass_dataset_api
@timing_decorator
@argument("search_parameters", type=QueryType())
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
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def search(
    dataset_api: DatasetApi,
    organization_id: str,
    search_parameters: str,
    output_file: Optional[str] = None,
    use_working_dir_file: bool = False,
    fields: str = None,
) -> CommandResponse:
    """Get all dataset having corresponding tag."""

    converted_search_parameters_content = get_api_file(api_file_path=search_parameters,
                                                       use_working_dir_file=use_working_dir_file)
    if converted_search_parameters_content is None:
        logger.error("Error : can not get correct dataset tag definition, please check your tag.YAML file")
        return CommandResponse.fail()

    try:
        retrieved_datasets = dataset_api.search_datasets(organization_id, converted_search_parameters_content)
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_datasets = filter_api_response(retrieved_datasets, fields.split(","))

    if output_file:
        _datasets_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_datasets]
        with open(output_file, "w") as _file:
            json.dump(_datasets_to_dump, _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s.", output_file)
    logger.info(pformat(retrieved_datasets, sort_dicts=False))
    return CommandResponse.success({"datasets": retrieved_datasets})
