import os
import sys
from json import dumps
from logging import getLogger

from click import echo, style

from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
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
    vars = env.get_variables()
    metadata = env.get_metadata(vars=vars, content=file_content, state=state)
    keycloak_token, config = get_keycloak_token()
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]
    api_section["solution_id"] = payload.get("id") or api_section.get("solution_id", "")
    if metadata.get("selector", ""):
        api_section["organization_id"] = metadata["selector"].get("organization_id", "")
    else:
        if not api_section["organization_id"]:
            logger.error(f"Missing 'organization_id' in metadata -> selector field : {metadata.get('selector')}")
            sys.exit(1)
    spec = dict()
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    solution_svc = SolutionService(keycloak_token=keycloak_token, spec=spec, config=config, state=api_section)
    sidecars = content.get("spec").get("sidecars", {})
    if not api_section["solution_id"]:
        logger.info("Creating solution")
        response = solution_svc.create()
        if response is None:
            return CommandResponse.fail()
        solution = response.json()
        logger.info(f"Solution {[solution['id']]} successfully created")
        state["services"]["api"]["solution_id"] = solution.get("id")
    else:
        logger.info(f"Updating solution {[api_section['solution_id']]}")
        response = solution_svc.update()
        if response is None:
            return CommandResponse.fail()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = solution_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        solution = response_json
        logger.info(f"Solution {[solution['id']]} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    # update run_templates
    if sidecars:
        run_scripts = sidecars.get("run_scripts")
        if run_scripts:
            data = run_scripts.get("post_deploy.sh", "")
            if data:
                os.system(data)
        if not solution.get("id"):
            sys.exit(1)
