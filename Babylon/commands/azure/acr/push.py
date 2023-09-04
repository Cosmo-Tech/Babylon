import docker
import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import get_docker_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@option("--image", type=QueryType(), help="Local docker image to push")
@timing_decorator
@inject_context_with_resource({'acr': ['login_server', 'simulator_repository', 'simulator_version']}, required=False)
def push(
    context: Any,
    image: Optional[str],
) -> CommandResponse:
    """
    Push a docker image to the ACR registry
    """
    registry_server = context['acr_login_server']
    image: str = image or f"{context['acr_simulator_repository']}:{context['acr_simulator_version']}"
    client = get_docker_client(registry_server)
    if not client:
        return CommandResponse.fail()
    try:
        image_obj = client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.error(f"Local image {image} not found")
        return CommandResponse.fail()

    logger.debug("Renaming image with registry prefix")
    ref_parts = image.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = registry_server
    else:
        ref_parts = [registry_server, *ref_parts]
    ref: str = "/".join(ref_parts)

    image_obj.tag(ref)

    logger.info(f"Pushing image {image} to {ref}")
    try:
        client.images.push(repository=ref)
    except docker.error.APIError as e:
        logger.error(f"Could not push image {image} to registry {registry_server}: {e}")
        return CommandResponse.fail()

    logger.debug("Removing local image with remote registry prefix")
    client.images.remove(ref)
    logger.info(f"Successfully pushed image {image} to registry {registry_server}")
    return CommandResponse.success()
