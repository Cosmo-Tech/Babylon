import logging
import typing

import docker
from click import command
from click import option

from ....utils.decorators import require_deployment_key
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.clients import get_docker_client

logger = logging.getLogger("Babylon")


@command()
@require_platform_key("csm_acr_registry_name", "csm_acr_registry_name")
@require_deployment_key("csm_simulator_repository", "csm_simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@require_deployment_key("simulator_repository", "simulator_repository")
@option("-r", "--registry", type=QueryType(), help="Container Registry name to pull from, ex: myregistry.azurecr.io")
@option("-i", "--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@timing_decorator
def pull(csm_acr_registry_name: str,
         csm_simulator_repository: str,
         simulator_repository: str,
         simulator_version: str,
         registry: typing.Optional[str] = None,
         image: typing.Optional[str] = None) -> CommandResponse:
    """Pulls a docker image from the ACR registry given in platform configuration.
       Also tag the docker image into the new reference (docker tag).
    """
    image = image or f"{csm_simulator_repository}:{simulator_version}"
    registry = registry or csm_acr_registry_name
    client = get_docker_client(registry)
    if not client:
        return CommandResponse.fail()
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
        return CommandResponse.fail()
    except docker.errors.APIError as api_error:
        logger.error(api_error)
        return CommandResponse.fail()
    except Exception as e:
        logger.error(str(e))
    logger.info(f"Successfully pulled image {image} from registry {registry}")
    return CommandResponse.success()
