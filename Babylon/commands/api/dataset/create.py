from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option
from rich.pretty import pprint

from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("dataset-name", required=False, type=QueryType())
@option("-c", "--connector-id", "connector_id", type=QueryType())
@require_deployment_key("organization_id", "organization_id")
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
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    organization_id: str,
    dataset_name: str,
    connector_id: Optional[str] = None,
    dataset_file: Optional[str] = None,
    dataset_description: Optional[str] = None,
) -> CommandResponse:
    """Register new dataset by sending description file to the API."""
    env = Environment()
    dataset_file = dataset_file or env.working_dir.payload_path / "api/dataset.json"
    details = env.fill_template(dataset_file,
                                data={
                                    "dataset_name": dataset_name,
                                    "connector_id": connector_id,
                                    "dataset_description": dataset_description
                                })
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    pprint(dataset)
    logger.info(f"Created new dataset with id: {dataset['id']}")
    return CommandResponse.success(dataset)
