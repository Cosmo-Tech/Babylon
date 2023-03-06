import logging
import typing

import docker
from click import command
from click import option

from ....utils.decorators import require_deployment_key
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from .registry_connect import registry_connect

logger = logging.getLogger("Babylon")


@command()
@require_platform_key("acr_registry_name", "acr_registry_name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@option("-i", "--image", type=QueryType(), help="Local docker image to push")
@option("-r", "--registry", type=QueryType(), help="Container Registry name to push to, example: myregistry.azurecr.io")
@timing_decorator
def push(acr_registry_name: str, simulator_repository: str, simulator_version: str, image: typing.Optional[str],
         registry: typing.Optional[str]) -> CommandResponse:
    """Push a docker image to the ACR registry given in platform configuration"""
    registry: str = registry or acr_registry_name
    image: str = image or f"{simulator_repository}:{simulator_version}"
    _, client = registry_connect(registry)
    try:
        image_obj = client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.error(f"Local image {image} not found")
        return CommandResponse.fail()

    logger.debug("Renaming image with registry prefix")
    ref_parts = image.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = registry
    else:
        ref_parts = [registry, *ref_parts]
    ref: str = "/".join(ref_parts)

    image_obj.tag(ref)

    logger.info(f"Pushing image {image} to {ref}")
    try:
        client.images.push(repository=ref)
    except docker.error.APIError as e:
        logger.error(f"Could not push image {image} to registry {registry}: {e}")
        return CommandResponse.fail()

    logger.debug("Removing local image with remote registry prefix")
    client.images.remove(ref)
    logger.info(f"Successfully pushed image {image} to registry {registry}")
    return CommandResponse.success()
