import json
import logging
import pathlib

from typing import Any, Optional
from click import command
from click import option
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
=======
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@option("--file",
        "config_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom config description file yaml")
@retrieve_state
def export_config(state: Any, config_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """
    Export webapp configuration in a json file
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzureWebAppService(state=service_state)
=======
    service = AzureWebAppService(state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.expor_config(config_file=config_file)
    return CommandResponse.success(json.loads(response))
