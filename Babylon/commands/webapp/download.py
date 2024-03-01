import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.environment import Environment
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@argument("destination_folder", type=Path(path_type=pathlib.Path))
@retrieve_state
def download(state: Any, destination_folder: pathlib.Path) -> CommandResponse:
    """
    Download the github repository locally
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzureWebAppService(state=service_state)
=======
    service = AzureWebAppService(state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    service.download(destination_folder=destination_folder)
    return CommandResponse.success()
