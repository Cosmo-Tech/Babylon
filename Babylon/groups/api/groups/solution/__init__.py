import cosmotech_api
from click import group
from click import pass_context
from click.core import Context
from cosmotech_api.api.solution_api import SolutionApi

from .commands import list_commands
from .....utils.decorators import pass_api_configuration


@group()
@pass_api_configuration
@pass_context
def solution(ctx: Context, api_configuration):
    """Subgroup handling Solution in the cosmotech API"""
    api_client = cosmotech_api.ApiClient(api_configuration)
    ctx.obj = SolutionApi(api_client)


for _command in list_commands:
    solution.add_command(_command)
