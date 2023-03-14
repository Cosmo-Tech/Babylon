import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import option
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.decorators import describe_dry_run
from ....utils.api import underscore_to_camel
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.decorators import output_to_file
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.api import camel_to_underscore
from ....utils.clients import pass_api_client
from ....utils.environment import Environment
from ....utils.api import convert_keys_case

logger = getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/api/Dataset.yaml"

@command()
@describe_dry_run("Would call **dataset_api.create_dataset**")
@timing_decorator
@pass_api_client
@require_deployment_key("organization_id", "organization_id")
@argument("dataset-name", required=False, type=QueryType())
@option("-c", "--connector-id", "connector_id", type=QueryType())
@option(
    "-d",
    "--description",
    "dataset_description",
    type=str,
    help="New dataset description",
)
@option(
    "-i",
    "--dataset-file",
    "dataset_file",
    type=str,
    help="Your custom dataset description file",
)
@output_to_file
def create(api_client: ApiClient,
           organization_id: str,
           dataset_name: str,
           connector_id: Optional[str] = None,
           dataset_description: Optional[str] = None,
           dataset_file: Optional[str] = None) -> CommandResponse:
    """Register new dataset by sending description file to the API."""
    dataset_api = DatasetApi(api_client)
    dataset_template = dataset_file or DEFAULT_PAYLOAD_TEMPLATE
    env = Environment()
    converted_dataset_content = convert_keys_case(
        env.fill_template(dataset_template,
                          data={
                              "dataset_name": dataset_name,
                              "connector_id": connector_id,
                              "dataset_description": dataset_description or dataset_name
                          }), camel_to_underscore)

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

    try:
        data = convert_keys_case(retrieved_dataset.to_dict(), underscore_to_camel)
    except AttributeError:
        data = convert_keys_case(retrieved_dataset, underscore_to_camel)
    logger.debug(pformat(data))
    logger.info(f"Created new dataset with id: {retrieved_dataset['id']}")
    return CommandResponse.success(data)
