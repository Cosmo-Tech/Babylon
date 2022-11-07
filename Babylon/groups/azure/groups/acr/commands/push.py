import logging
from typing import Optional

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
@require_platform_key("acr_dest_registry_name")
@require_deployment_key("simulator_repository")
@require_deployment_key("simulator_version")
@option("-i", "--image", help="Local docker image to push")
@option("-r", "--registry", help="Container Registry name to push to, example: myregistry.azurecr.io")
def push(credentials: DefaultAzureCredential,
         acr_dest_registry_name: str,
         simulator_repository: str,
         simulator_version: str,
         image: Optional[str] = None,
         registry: Optional[str] = None):
    """Push a docker image to the ACR registry given in platform configuration"""
    registry_dest: str = registry or acr_dest_registry_name
    image_dest: str = image or f"{simulator_repository}:{simulator_version}"
    _, client = registry_connect(registry_dest, credentials)
    try:
        image_obj = client.images.get(image_dest)
    except docker.errors.ImageNotFound:
        logger.error(f"Local image {image_dest} not found")
        return

    logger.debug("Renaming image with registry prefix")
    ref_parts = image_dest.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = registry_dest
    else:
        ref_parts = [registry_dest, *ref_parts]
    ref: str = "/".join(ref_parts)

    image_obj.tag(ref)

    logger.info(f"Pushing image {image_dest} to {ref}")
    try:
        client.images.push(repository=ref)
    except docker.error.APIError as e:
        logger.error(f"Could not push image {image_dest} to registry {registry_dest}: {e}")
        return

    logger.debug("Removing local image with remote registry prefix")
    client.images.remove(ref)

    logger.info(f"Successfully pushed image {image_dest} to registry {registry_dest}")
