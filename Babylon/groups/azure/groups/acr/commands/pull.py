import logging
import typing

from azure.identity import DefaultAzureCredential
from click import command
from click import option
from click import make_pass_decorator

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......modules.azure.acr import AzureAcr

logger = logging.getLogger("Babylon")

pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("acr_src_registry_name", "acr_src_registry_name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@option("-r", "--registry", help="Container Registry name to pull from, example: myregistry.azurecr.io")
@option("-i", "--image", help="Remote docker image to pull, example hello-world:latest")
def pull(credentials: DefaultAzureCredential,
         acr_src_registry_name: str,
         simulator_repository: str,
         simulator_version: str,
         registry: typing.Optional[str] = None,
         image: typing.Optional[str] = None):
    """Pulls a docker image from the ACR registry given in platform configuration"""
    image = image or f"{simulator_repository}:{simulator_version}"
    registry = registry or acr_src_registry_name
    acr = AzureAcr()
    acr.connect(credentials, registry)
    acr.pull(image)
