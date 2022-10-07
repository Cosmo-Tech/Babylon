import os
import logging
import docker
from click import command, pass_context
from click.core import Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import requires_external_program, require_deployment_key

logger = logging.getLogger("Babylon")

"""Command Tests
> babylon acr pull
Should provide a clean error log
> babylon acr pull
Should provide a clean error log
> babylon acr pull
Should add a new entry to `docker image ls`
> babylon acr pull
Should a new entry to `docker image ls` with the latest tag
"""

@command()
@requires_external_program("docker")
@pass_context
@require_deployment_key("acr_src_registry_name", "acr_src_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
def pull(ctx: Context, acr_src_registry_name: str, acr_image_reference: str):
    """Pulls a docker image from the ACR registry given in deployment configuration"""
    # Login to registry
    os.system(f"az acr login --name {acr_src_registry_name}")
    ContainerRegistryClient(
        f"https://{acr_src_registry_name}",
        ctx.parent.obj,
        audience="https://management.azure.com")
    # Pulling image
    client = docker.from_env()
    logger.info("Pulling image %s", acr_image_reference)
    repo = f"{acr_src_registry_name}/{acr_image_reference}"
    try:
        client.images.pull(repository=repo)
    except docker.errors.NotFound:
        logger.error("Registry %s does not contain %s", acr_src_registry_name, acr_image_reference)
    except docker.errors.APIError as api_error:
        logger.error("API Error: %s", api_error)
