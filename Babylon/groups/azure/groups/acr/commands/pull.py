import logging
import docker
from click import command, make_pass_decorator, argument, option
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import requires_external_program, require_deployment_key

logger = logging.getLogger("Babylon")

"""Command Tests
> babylon acr pull this_image_does_not_exist
Should provide a clean error log
> babylon acr pull existing_image -t tag_that_does_not_exists
Should provide a clean error log
> babylon acr pull existing_image -t existing_tag
Should add a new entry to `docker image ls`
> babylon acr pull existing_image
Should a new entry to `docker image ls` with the latest tag
"""

pass_cr_client = make_pass_decorator(ContainerRegistryClient)

@command()
@requires_external_program("docker")
@pass_cr_client
@require_deployment_key("acr_registry_name", "acr_registry_name")
@argument("image")
@option("-t", "--tag", default="latest", show_default=True)
def pull(cr_client: ContainerRegistryClient, acr_registry_name: str, image: str, tag: str):
    """Pulls a docker image from the ACR registry given in deployment configuration"""
    client = docker.from_env()
    logger.info("Pulling image %s:%s", image, tag)
    repo = f"{acr_registry_name}.azurecr.io/{image}" if ".azurecr.io/" not in image else image
    try:
        client.images.pull(repository=repo, tag=tag)
    except docker.errors.NotFound:
        logger.error("Registry %s does not contain %s:%s", acr_registry_name, image, tag)
    except docker.errors.APIError as api_error:
        logger.error("API Error: %s", api_error)
