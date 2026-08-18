import logging
from typing import Any

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("dataset_id", type=str)
@retrieve_state
def update_credentials(
    state: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Update the credentials of a dataset's datasources using Basic authentication.
    """
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve postgreSQL configuration from secret 'postgresql-cosmotechapi'")
        return CommandResponse.fail()

    tenant = env.environ_id
    clean_prefix = tenant.replace("-", "_")
    writer_username = f"{clean_prefix}_cosmotech_api_writer"
    writer_password = api_config.get("writer-password", "")
    if not writer_username or not writer_password:
        logger.error("  [bold red]✘[/bold red] Writer credentials not found in secret 'postgresql-cosmotechapi'")
        return CommandResponse.fail()

    service_state = state["services"]
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
    service.update_credentials(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        username=writer_username,
        password=writer_password,
    )
    return CommandResponse()
