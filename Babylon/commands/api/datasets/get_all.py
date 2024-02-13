from logging import getLogger
from typing import Any, Optional

import jmespath
from click import command
from click import option
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, organization_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all datasets from the organization
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    logger.info(f"Getting all datasets from organization {service_state['api']['organization_id']}")
    service = DatasetService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    datasets = response.json()
    if len(datasets) and filter:
        datasets = jmespath.search(filter, datasets)
    return CommandResponse.success(datasets, verbose=True)
