import logging
from click import command, make_pass_decorator
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import requires_external_program, require_deployment_key

logger = logging.getLogger("Babylon")

"""Command Tests
> babylon acr ls
Should list all images in the given registry
Can be checked against `az acr repository list --name my_registry --output table`
"""

pass_cr_client = make_pass_decorator(ContainerRegistryClient)

@command()
@requires_external_program("docker")
@pass_cr_client
@require_deployment_key("acr_registry_name", "acr_registry_name")
def ls(cr_client: ContainerRegistryClient, acr_registry_name: str):
    """List all docker images in the specified registry"""
    logger.info("Getting repositories stored in registry %s", acr_registry_name)
    for repo in cr_client.list_repository_names():
        logger.info("repository: %s", repo)
