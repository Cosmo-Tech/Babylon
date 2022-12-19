import logging
import typing

import docker
from azure.identity import DefaultAzureCredential
from click import command
from click import make_pass_decorator
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator
from ......utils.typing import QueryType
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")
pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("csm_acr_registry_name", "csm_acr_registry_name")
@require_deployment_key("csm_simulator_repository", "csm_simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@require_deployment_key("simulator_repository", "simulator_repository")
@option("-r", "--registry", type=QueryType(), help="Container Registry name to pull from, ex: myregistry.azurecr.io")
@option("-i", "--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@timing_decorator
def pull(credentials: DefaultAzureCredential,
         cms_acr_registry_name: str,
         cms_simulator_repository: str,
         simulator_repository: str,
         simulator_version: str,
         registry: typing.Optional[str] = None,
         image: typing.Optional[str] = None):
    """Pulls a docker image from the ACR registry given in platform configuration"""
    image = image or f"{cms_simulator_repository}:{simulator_version}"
    registry = registry or cms_acr_registry_name
    _, client = registry_connect(registry, credentials)
    repo = f"{registry}/{image}"
    logger.info(f"Pulling remote image {image} from registry {registry}")
    try:
        img = client.images.pull(repository=repo)
        logger.debug("Renaming local image without registry prefix")
        img.tag(f"{simulator_repository}:{simulator_version}")
        logger.debug("Removing local image with registry prefix")
        client.images.remove(image=repo)
    except docker.errors.NotFound:
        logger.error(f"Image {image} not found in registry {registry} ")
        return
    except docker.errors.APIError as api_error:
        logger.error(api_error)
        return
    except Exception as e:
        logger.error(str(e))
    logger.info(f"Successfully pulled image {image} from registry {registry}")
