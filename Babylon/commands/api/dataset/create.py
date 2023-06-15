from logging import getLogger
from typing import Optional
import pathlib

from click import argument
from click import command
from click import option
from click import Path

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("dataset-name", type=QueryType(), default="")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("-i",
        "--dataset-file",
        "dataset_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom dataset description file (yaml or json)")
@option(
    "-d",
    "--description",
    "dataset_description",
    help="New dataset description",
)
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new dataset in configuration ?",
)
@option("-t", "--type", "dataset_type", type=QueryType())
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    dataset_name: str,
    organization_id: str,
    dataset_type: str,
    dataset_file: Optional[pathlib.Path] = None,
    dataset_description: Optional[str] = None,
    select: bool = False,
) -> CommandResponse:
    """
    Register a dataset by sending a description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    if not dataset_type:
        logger.error("Dataset type not found")
        return CommandResponse.fail()
    
    dataset_type = dataset_type.lower()
    dataset_file = dataset_file or env.working_dir.payload_path / f"api/dataset.{dataset_type}.yaml"
    connector_id = env.configuration.get_deploy_var(f"{dataset_type}_connector_id")
    details = env.fill_template(dataset_file,
                                data={
                                    "dataset_name": dataset_name,
                                    "connector_id": connector_id,
                                    "dataset_description": dataset_description
                                })
    if dataset_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(f"Successfully created dataset {dataset['id']}")
    if select:
        logger.info("Updated configuration variables with dataset_id")
        env.configuration.set_deploy_var(f"{dataset_type}_dataset_id", dataset["id"])
    return CommandResponse.success(dataset, verbose=True)
