import pathlib
from logging import getLogger
from typing import Any

from click import Path
from click import argument
from click import command
from click import option

from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.checkers import check_ascii
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option(
    "--file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom solution description file (yaml or json)", )
@argument("name", type=QueryType())
@retrieve_state
def create(state: Any, azure_token: str, organization_id: str, solution_name: str,
           solution_file: pathlib.Path) -> CommandResponse:
    """
    Register a new solution
    """
    state = state['services']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']

    check_ascii(solution_name)
    path_file = f"{env.context_id}.{env.environ_id}.solution.yaml"
    t_file = solution_file or env.working_dir.payload_path / path_file
    details = env.fill_template(t_file,
                                data={
                                    "key": solution_name.replace(" ", ""),
                                    "name": solution_name,
                                    'tag': env.context_id.capitalize()
                                })
    spec = {"data": details}

    service = SolutionService(state=state, azure_token=azure_token, spec=spec)
    response = service.create()
    created_solution = response.json()

    if response is None:
        return CommandResponse.fail()
    state["api"]["solution_id"] = created_solution["id"]
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(SUCCESS_CONFIG_UPDATED("api", "solution_id"))
    logger.info(SUCCESS_CREATED("solution", created_solution["id"]))
    return CommandResponse.success(created_solution, verbose=True)
