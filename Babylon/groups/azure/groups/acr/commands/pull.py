import logging
import typing

import docker
from click import command
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ....connect import azure_connect
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")


@command()
@require_platform_key("acr_src_registry_name", "acr_src_registry_name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@option("-r", "--registry", help="Container Registry name to pull from, example: myregistry.azurecr.io")
@option("-i", "--image", help="Remote docker image to pull, example hello-world:latest")
def pull(acr_src_registry_name: str,
         simulator_repository: str,
         simulator_version: str,
         registry: typing.Optional[str] = None,
         image: typing.Optional[str] = None):
    """Pulls a docker image from the ACR registry given in platform configuration"""
    image = image or f"{simulator_repository}:{simulator_version}"
    registry = registry or acr_src_registry_name
    credentials = azure_connect()
    _, client = registry_connect(registry, credentials)
    repo = f"{registry}/{image}"
    logger.info(f"Pulling remote image {image} from registry {registry}")
    try:
        img = client.images.pull(repository=repo)
        logger.debug("Renaming local image without registry prefix")
        img.tag(image)
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
