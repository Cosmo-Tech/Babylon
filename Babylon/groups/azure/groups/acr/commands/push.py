import json
import logging
import typing

import docker
from azure.identity import DefaultAzureCredential
from click import command
from click import make_pass_decorator
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")
pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("acr_dest_registry_name", "acr_dest_registry_name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@option("-i", "--image", help="Local docker image to push")
@option("-r", "--registry", help="Container Registry name to push to, example: myregistry.azurecr.io")
def push(credentials: DefaultAzureCredential, acr_dest_registry_name: str, simulator_repository: str,
         simulator_version: str, image: typing.Optional[str], registry: typing.Optional[str]):
    """Push a docker image to the ACR registry given in platform configuration"""
    registry: str = registry or acr_dest_registry_name
    image: str = image or f"{simulator_repository}:{simulator_version}"
    _, client = registry_connect(registry, credentials)
    try:
        image_obj = client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.error(f"Image {image} not found locally")
        return
    logger.info(f"Pushing image {image}")

    # Rename image with registry url if it is not present
    ref_parts = image.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = registry
    else:
        ref_parts = [registry, *ref_parts]
    ref: str = "/".join(ref_parts)

    # Rename image with remote repository prefix
    image_obj.tag(ref)

    logs: str = client.images.push(repository=ref)

    # Remove image with remote repository prefix
    client.images.remove(ref)
    # Log status
    for resp in logs.split("\n"):
        if not resp:
            continue
        decoded = json.loads(resp)
        status = decoded.get("status")
        if status:
            logger.info(status)
        error = decoded.get("errorDetail")
        if error:
            logger.error(error.get("message"))
