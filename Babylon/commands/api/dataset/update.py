from logging import getLogger
import pathlib
from typing import Optional

from click import Path, argument
from click import command
from click import option

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import require_deployment_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@require_deployment_key("organization_id")
@pass_azure_token("csm_api")
@argument("dataset_id", type=QueryType(), default="")
@option("-t", "--type", "dataset_type", type=QueryType())
@option("-i",
        "--dataset-file",
        "dataset_file",
        type=Path(path_type=pathlib.Path),
        required=True,
        help="Your custom dataset description file (yaml or json)")
# @output_to_file
def update(
        api_url: str,
        azure_token: str,
        organization_id: str,
        dataset_type: str,
        dataset_file: pathlib.Path,
        dataset_id: Optional[str] = None,
    ) -> CommandResponse:
    """
    Register new dataset by sending description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    if not dataset_type:
        logger.error("Dataset type not found")
        return CommandResponse.fail()
    
    dataset_type = dataset_type.lower()
    if not dataset_id:
        dataset_id = env.configuration.get_deploy_var(f"{dataset_type}_dataset_id")
    dataset = oauth_request(f"{api_url}/organizations/{organization_id}/datasets/{dataset_id}",
                            azure_token,
                            type="GET")
    dataset = dataset.json()
    details = env.fill_template(dataset_file,
                                data={
                                    "dataset_name": dataset['name'],
                                    "connector_id": dataset['connector']['id'],
                                    "dataset_description": dataset['description']
                                })
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
