from logging import getLogger

from click import command

from ....utils.environment import Environment
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
    """Delete all connectors from the registered organization"""

    if not confirm_deletion("all registered connectors in current configuration", organization_id):
        return CommandResponse.fail()
    logger.info(f"Getting all connectors from organization {organization_id}")

    env = Environment()

    connectors = [env.configuration.get_deploy_var(key) for key in ("adt_connector_id", "storage_connector_id")]

    for connector in connectors:
        if connector is None:
            continue
        logger.info(f"Deleting connector {connector}")
        response = oauth_request(f"{api_url}/connectors/{connector}", azure_token, type="DELETE")

    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted all connectors from organization {organization_id}")
    return CommandResponse.success()
