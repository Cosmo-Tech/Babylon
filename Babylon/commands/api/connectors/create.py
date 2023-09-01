import logging
import pathlib
from posixpath import basename
import sys

from typing import Any, Optional
from click import Choice, Context, Path, pass_context
from click import argument
from click import command
from click import option
from Babylon.utils.messages import SUCCESS_CREATED
from Babylon.utils.checkers import check_alphanum
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_context
@pass_azure_token("csm_api")
@option("--file",
        "connector_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom connector description file (yaml or json)")
@option("--select", "select", is_flag=True, default=True, help="Save the connector in configuration")
@option("--type", "type", type=Choice(['adt', 'storage', 'twin']), required=True)
@option("--version", "version", type=QueryType(), required=True)
@argument("name", type=QueryType(), required=True)
@output_to_file
@inject_context_with_resource({"api": ["url"]})
def create(
    ctx: Context,
    context: Any,
    azure_token: str,
    name: str,
    type: str,
    version: str,
    connector_file: Optional[pathlib.Path] = None,
    select: bool = False,
) -> CommandResponse:
    """
    Register a new Connector
    """
    check_alphanum(name)
    path_file = f"{env.context_id}.{env.environ_id}.connector.{type}.yaml"
    connector_file = connector_file or env.working_dir.payload_path / path_file
    if not connector_file.exists():
        logger.error(f"No such file: '{basename(connector_file)}' in .payload directory")
        sys.exit(1)
    if type not in connector_file.name:
        logger.error(f"Connector type {type} error")
        return CommandResponse.fail()

    type = type.lower()
    details = env.fill_template(connector_file,
                                data={
                                    "tag": env.context_id.capitalize(),
                                    "name": name,
                                    "key": name.replace(" ", ""),
                                    "version": version
                                })
    key_name = ["connector", f"{type}_id"]
    response = oauth_request(f"{context['api_url']}/connectors", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name=key_name,
                                  var_value=connector['id'])
    logger.info(SUCCESS_CREATED("connector", connector["id"]))
    return CommandResponse.success(connector, verbose=True)
