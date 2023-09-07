import pathlib
from logging import getLogger

from click import argument
from click import command
from click import option
from click import Path

from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--dataset-id", "dataset_id", type=QueryType(), default="%deploy%dataset_id")
@argument("dataset_file", type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@output_to_file
def update(
    api_url: str,
    azure_token: str,
    organization_id: str,
    dataset_id: str,
    dataset_file: pathlib.Path,
) -> CommandResponse:
    """
    Register new dataset by sending description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    details = env.fill_template(dataset_file)
    if dataset_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets/{dataset_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(f"Successfully updated dataset {dataset['id']}")
    return CommandResponse.success(dataset, verbose=True)
