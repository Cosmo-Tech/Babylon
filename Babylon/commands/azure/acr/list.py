import logging

from typing import Any, Optional
from azure.core.exceptions import ServiceRequestError
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import get_registry_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@argument("server", type=QueryType(), required=False)
@inject_context_with_resource({'acr': ['login_server']})
def list(context: Any, server: Optional[str] = None) -> CommandResponse:
    """
    List all docker images in the specified registry
    """
    acr_login_server = server or context['acr_login_server']
    cr_client = get_registry_client(acr_login_server)
    logger.info(f"Getting repositories stored in registry {acr_login_server}")
    try:
        repos = [repo for repo in cr_client.list_repository_names()]
    except ServiceRequestError:
        logger.error(f"Could not list from registry {acr_login_server}")
        return CommandResponse.fail()
    _ret: list[str] = [f"Respositories from {acr_login_server}:"]
    for repo in repos:
        props = cr_client.list_tag_properties(repository=repo)
        tags = [p.name for p in props]
        tags.sort(reverse=True)
        _ret.append(f" • {repo}: {tags}")
    logger.info("\n".join(_ret))
    CommandResponse.success()
