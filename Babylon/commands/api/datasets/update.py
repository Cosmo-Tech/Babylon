import pathlib

from logging import getLogger
from typing import Any
from click import Choice, Path, argument
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource, output_to_file, timing_decorator, wrapcontext
from Babylon.utils.messages import SUCCESS_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--type",
        "type",
        type=Choice(['adt', 'storage', 'twin']),
        required=True,
        help="Dataset type Cosmotech Platform")
@option("--file",
        "dataset_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom dataset description file (yaml or json)")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id']})
def update(
    context: Any,
    azure_token: str,
    type: str,
    dataset_file: pathlib.Path,
    id: str,
) -> CommandResponse:
    """
    update a registered dataset
    """
    type = type.lower()
    path_file = f"{env.context_id}.{env.environ_id}.dataset.{type}.yaml"
    dataset_file = dataset_file or env.working_dir.payload_path / path_file
    if not dataset_file.exists():
        return CommandResponse.fail()
    details = env.fill_template(dataset_file)
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/datasets/{id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(SUCCESS_UPDATED("dataset", dataset['connector']['id']))
    return CommandResponse.success(dataset, verbose=True)
