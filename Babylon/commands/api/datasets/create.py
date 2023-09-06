import pathlib

from logging import getLogger
from posixpath import basename
import sys
from typing import Any, Optional
from click import Choice, Context, argument, pass_context
from click import command
from click import option
from click import Path
from Babylon.utils.checkers import check_alphanum
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--file",
        "dataset_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom dataset description file (yaml or json)")
@option("--select", "select", is_flag=True, default=True, help="Save this dataset in configuration")
@option("--type", "type", type=Choice(['adt', 'storage']), required=True, help="Dataset type Cosmotech Platform")
@argument("name", type=QueryType())
@inject_context_with_resource({'api': ['url', 'organization_id', 'connector']})
def create(
    ctx: Context,
    context: Any,
    azure_token: str,
    name: str,
    type: str,
    select: bool,
    dataset_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Register a dataset
    """
    check_alphanum(name)
    connector_id = context['api_connector'][f"{type}_id"]
    if not connector_id:
        logger.error(f"You trying to use '{env.context_id}.{env.environ_id}.api.yaml' configuration")
        logger.error(f"Connector {type}_id is missing")
        return CommandResponse.fail()
    path_file = f"{env.context_id}.{env.environ_id}.dataset.{type}.yaml"
    dataset_file = dataset_file or env.working_dir.payload_path / path_file
    if not dataset_file.exists():
        logger.error(f"No such file: '{basename(dataset_file)}' in .payload directory")
        sys.exit(1)
    details = env.fill_template(dataset_file,
                                data={
                                    "name": name,
                                    "connector_id": connector_id,
                                    "tag": type.capitalize()
                                })
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/datasets",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    if select:
        var_name = ["dataset", f"{type}_id"]
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name=var_name,
                                  var_value=dataset["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("dataset", f"dataset.{type}_id"))
    logger.info(SUCCESS_CREATED("dataset", dataset['id']))
    return CommandResponse.success(dataset, verbose=True)
