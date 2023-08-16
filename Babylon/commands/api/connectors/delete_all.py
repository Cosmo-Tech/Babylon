from logging import getLogger
from typing import Any
from click import Context, command, pass_context
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.messages import SUCCESS_DELETED

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@inject_context_with_resource({"api": ['url', 'organization_id']})
def delete_all(ctx: Context, context: Any, azure_token: str, force_validation: bool = False) -> CommandResponse:
    """Delete all connectors from the current configuration"""
    logger.info("Geting all connectors from current configuration...")
    connectors = env.configuration.get_var(resource_id=ctx.parent.parent.command.name, var_name="connector")
    response = None
    for key, connector_id in connectors.items():
        if connector_id == '':
            break
        if not force_validation and not confirm_deletion(ctx.parent.command.name, connector_id):
            return CommandResponse.fail()
        logger.info(f"Deleting {ctx.parent.command.name} {key}")
        response = oauth_request(f"{context['api_url']}/connectors/{connector_id}", azure_token, type="DELETE")
        logger.info(SUCCESS_DELETED("connector", connector_id))
        if response is None:
            return CommandResponse.fail()
    return CommandResponse.success()
