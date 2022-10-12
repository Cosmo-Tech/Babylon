import logging
import subprocess
import typing

from azure.containerregistry import ContainerRegistryClient
from click import command
from click import Context
from click import option
from click import pass_context

from ......utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure acr ls
Should list all images in the registry given in config
> babylon azure acr ls -r my_registry
Should list all images in the given registry
Can be checked against `az acr repository list --name my_registry --output table`
"""


@command()
@pass_context
@require_deployment_key("acr_src_registry_name", "acr_src_registry_name")
@option("-r", "--registry", help="Container Registry name to scan, example: myregistry.azurecr.io")
def ls(ctx: Context, acr_src_registry_name: str, registry: typing.Optional[str]):
    """List all docker images in the specified registry"""
    registry = registry or acr_src_registry_name
    # Login to registry
    response = subprocess.run(["az", "acr", "login", "--name", registry],
                              shell=False,
                              check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    if response.returncode:
        logger.error(f"Could not connect to registry {registry}: {response.stderr}")
        return
    cr_client = ContainerRegistryClient(f"https://{registry}", ctx.parent.obj, audience="https://management.azure.com")
    logger.info("Getting repositories stored in registry %s", registry)
    for repo in cr_client.list_repository_names():
        logger.info(f"repository: {repo}")
