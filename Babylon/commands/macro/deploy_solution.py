from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.solution_create_request import SolutionCreateRequest
from cosmotech_api.models.solution_security import SolutionSecurity
from cosmotech_api.models.solution_update_request import SolutionUpdateRequest

from Babylon.commands.api.client import get_solution_api_instance
from Babylon.commands.macro.deploy import update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_solution(namespace: str, file_content: str) -> bool:
    _ret = [""]
    _ret.append("Solution deployment")
    _ret.append("")
    echo(style("\n".join(_ret), bold=True, fg="green"))
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()

    keycloak_token, config = get_keycloak_token()
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]
    api_section["solution_id"] = payload.get("id") or api_section.get("solution_id", "")

    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    api_instance = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
    if not api_section["solution_id"]:
        logger.info("Creating solution")
        solution_create_request = SolutionCreateRequest.from_dict(payload)
        solution = api_instance.create_solution(
            organization_id=api_section["organization_id"], solution_create_request=solution_create_request
        )
        if solution is None:
            return CommandResponse.fail()
        logger.info(f"Solution {solution.id} successfully created")
        state["services"]["api"]["solution_id"] = solution.id
    else:
        logger.info(f"Updating solution {api_section['solution_id']}")
        solution_update_request = SolutionUpdateRequest.from_dict(payload)
        updated = api_instance.update_solution(
            organization_id=api_section["organization_id"],
            solution_id=api_section["solution_id"],
            solution_update_request=solution_update_request,
        )

        if updated is None:
            return CommandResponse.fail()
        if payload.get("security"):
            try:
                current_security = api_instance.get_solution_security(
                    organization_id=api_section["organization_id"], solution_id=api_section["solution_id"]
                )
                update_object_security(
                    "solution",
                    current_security=current_security,
                    desired_security=SolutionSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=[api_section["organization_id"], api_section["solution_id"]],
                )
            except Exception as e:
                logger.error(f"Failed to update solution security: {e}")
                return CommandResponse.fail()
        logger.info(f"Solution {api_section['solution_id']} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
