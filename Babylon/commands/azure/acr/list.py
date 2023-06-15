import logging
import typing

from azure.core.exceptions import ServiceRequestError
from click import Choice
from click import command
from click import option

from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.clients import get_registry_client

logger = logging.getLogger("Babylon")


@command()
@require_platform_key("csm_acr_registry_name")
@require_platform_key("acr_registry_name")
@option("-r", "--registry", type=QueryType(), help="Container Registry name to scan, example: myregistry.azurecr.io")
@option("-d", "--direction", type=Choice(["src", "dest"]), help="Container Registry choice to delete from")
@timing_decorator
def list(
        csm_acr_registry_name: str,
        acr_registry_name: str, registry: typing.Optional[str],
        direction: typing.Optional[str]
    ) -> CommandResponse:
    """List all docker images in the specified registry"""
    registry = registry or {"src": csm_acr_registry_name, "dest": acr_registry_name}.get(direction)
    if not registry:
        logger.error("Please specify a registry to list from with --direction or --registry")
        return CommandResponse.fail()
    cr_client = get_registry_client(registry)
    logger.info("Getting repositories stored in registry %s", registry)
    try:
        repos = [repo for repo in cr_client.list_repository_names()]
    except ServiceRequestError:
        logger.error(f"Could not list from registry {registry}")
        return CommandResponse.fail()
    logger.info(repos)
    return CommandResponse.success({"repositories": repos})
