from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-part-id", "dataset_part_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete_part(state: Any,
                keycloak_token: str,
                organization_id: str,
                workspace_id: str,
                dataset_id: str,
                dataset_part_id: str,
                force_validation: bool = False) -> CommandResponse:
    """Delete a dataset part"""
    _data = [""]
    _data.append("Delete a dataset part")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Deleting dataset part {dataset_part_id} from dataset {[service_state['api']['dataset_id']]}")
    response = service.delete_part(dataset_part_id, force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"[api] Dataset part {dataset_part_id} successfully deleted")
    return CommandResponse.success(response)
