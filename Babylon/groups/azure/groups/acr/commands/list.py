import logging
import typing

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ServiceRequestError
from click import Choice
from click import command
from click import option
from click import pass_context
from click import Context

from ......utils.decorators import require_platform_key
from ......utils.response import CommandResponse
from ......utils.response import CommandStatus
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("acr_src_registry_name", "acr_src_registry_name")
@require_platform_key("acr_dest_registry_name", "acr_dest_registry_name")
@option("-r", "--registry", help="Container Registry name to scan, example: myregistry.azurecr.io")
@option("-d", "--direction", type=Choice(["src", "dest"]), help="Container Registry choice to delete from")
def list(ctx: Context, acr_src_registry_name: str, acr_dest_registry_name: str, registry: typing.Optional[str],
         direction: typing.Optional[str]) -> CommandResponse:
    """List all docker images in the specified registry"""
    credentials: DefaultAzureCredential = ctx.find_object(DefaultAzureCredential)
    registry = registry or {"src": acr_src_registry_name, "dest": acr_dest_registry_name}.get(direction)
    if not registry:
        logger.error("Please specify a registry to list from with --direction or --registry")
        return CommandResponse(ctx.command, ctx.params, status_code=CommandStatus.ERROR)
    cr_client, _ = registry_connect(registry, credentials)
    logger.info("Getting repositories stored in registry %s", registry)
    try:
        repos = [repo for repo in cr_client.list_repository_names()]
    except ServiceRequestError:
        logger.error(f"Could not list from registry {registry}")
        return CommandResponse(ctx.command, ctx.params, status_code=CommandStatus.ERROR)
    logger.info(repos)
    return CommandResponse(ctx.command, ctx.params, data={"repositories": repos})
