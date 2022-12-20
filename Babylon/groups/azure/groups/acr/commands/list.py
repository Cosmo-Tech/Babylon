import logging
import typing

from azure.core.exceptions import ServiceRequestError
from azure.identity import DefaultAzureCredential
from click import Choice
from click import command
from click import make_pass_decorator
from click import option

from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.typing import QueryType
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")

pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("csm_acr_registry_name", "csm_acr_registry_name")
@require_platform_key("acr_registry_name", "acr_registry_name")
@option("-r", "--registry", type=QueryType(), help="Container Registry name to scan, example: myregistry.azurecr.io")
@option("-d", "--direction", type=Choice(["src", "dest"]), help="Container Registry choice to delete from")
@timing_decorator
def list(credentials: DefaultAzureCredential, csm_acr_registry_name: str, acr_registry_name: str,
         registry: typing.Optional[str], direction: typing.Optional[str]) -> CommandResponse:
    """List all docker images in the specified registry"""
    registry = registry or {"src": csm_acr_registry_name, "dest": acr_registry_name}.get(direction)
    if not registry:
        logger.error("Please specify a registry to list from with --direction or --registry")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    cr_client, _ = registry_connect(registry, credentials)
    logger.info("Getting repositories stored in registry %s", registry)
    try:
        repos = [repo for repo in cr_client.list_repository_names()]
    except ServiceRequestError:
        logger.error(f"Could not list from registry {registry}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(repos)
    return CommandResponse(data={"repositories": repos})
