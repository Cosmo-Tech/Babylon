import logging
from click import command, make_pass_decorator
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import requires_external_program, require_deployment_key

logger = logging.getLogger("Babylon")

pass_cr_client = make_pass_decorator(ContainerRegistryClient)

@command()
@requires_external_program("docker")
@pass_cr_client
@require_deployment_key("acr_registry_url", "acr_registry_url")
def ls(cr_client: ContainerRegistryClient, acr_registry_url: str):
    """List all docker images in the specified registry"""
    logger.info("Getting repositories stored in registry %s", acr_registry_url)
    for repo in cr_client.list_repository_names():
        logger.info("image: %s", repo)
