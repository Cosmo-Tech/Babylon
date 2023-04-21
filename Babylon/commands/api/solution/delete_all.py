from logging import getLogger

from click import command

from ....utils.interactive import confirm_deletion
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import require_platform_key, require_deployment_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@require_deployment_key("organization_id")
@pass_azure_token("csm_api")
def delete_all(api_url: str, azure_token: str, organization_id: str) -> CommandResponse:
    """Delete all solutions from the registered organization"""

    if not confirm_deletion("all solutions of organization", organization_id):
        return CommandResponse.fail()
    logger.info(f"Getting all solutions from organization {organization_id}")
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions", azure_token)
    if response is None:
        return CommandResponse.fail("Unable to retrieve solutions for this organization")
    solutions = response.json()

    for solution in solutions:
        logger.info(f"Deleting solution {solution['id']}")
        response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions/{solution['id']}", azure_token, type="DELETE")

    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted all solutions from organization {organization_id}")
    return CommandResponse.success()
