from logging import getLogger
from typing import Any
from click import command
from Babylon.services.organizations_service import OrganizationService
from Babylon.commands.api.connectors.service.api import ConnectorService
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@retrieve_state
def destroy(state: Any, azure_token: str) -> CommandResponse:
    """
    Clean up the API objects
    """
    service_state = state["services"]
    try:
        if service_state["api"]["organization_id"]:
            organization_service = OrganizationService(service_state, azure_token)
            organization_service.delete(True)
            service_state["api"]["organization_id"] = ""
        if state["services"]["api"]["connector_id"]:
            connector_service = ConnectorService(state, azure_token)
            connector_service.delete(True)
            state["services"]["api"]["connector_id"] = ""
        if state["services"]["api"]["dataset_id"]:
            dataset_service = DatasetService(state, azure_token)
            dataset_service.delete(True)
            state["services"]["api"]["dataset_id"] = ""
        if state["services"]["api"]["scenario_id"]:
            scenario_service = ScenarioService(state, azure_token)
            scenario_service.delete(True)
            state["services"]["api"]["scenario_id"] = ""
        if state["services"]["api"]["solution_id"]:
            solution_service = SolutionService(state, azure_token)
            solution_service.delete(True)
            state["services"]["api"]["solution_id"] = ""
        if state["services"]["api"]["workspace_id"]:
            workspace_service = SolutionService(state, azure_token)
            workspace_service.delete(True)
            state["services"]["api"]["workspace_id"] = ""

        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
    except Exception as e:
        error_message = f"Error while destroying the API objects: {e}"
        logger.error(error_message)
        return CommandResponse.error(error_message)
    return CommandResponse.success()
