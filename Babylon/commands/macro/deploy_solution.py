import os
import sys
import json
import click

from logging import getLogger

from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_keycloak_token
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


def deploy_solution(namespace: str, file_content: str) -> bool:
    _ret = [""]
    _ret.append("Solution deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url = env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func(state_id=env.state_id)
    state["services"]["api"]["url"] = platform_url
    state["services"]["azure"]["tenant_id"] = env.tenant_id
    vars = env.get_variables()
    metadata = env.get_metadata(vars=vars, content=file_content, state=state)
    workspace_key = metadata.get(
        "workspace_key",
        vars.get("workspace_key", state["services"]["api"]["workspace_key"]),
    )
    state["services"]["api"]["workspace_key"] = workspace_key
    keycloak_token = get_keycloak_token()
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    state["services"]["api"]["solution_id"] = (payload.get("id") or state["services"]["api"]["solution_id"])
    if metadata.get("selector", ""):
        state["services"]["api"]["organization_id"] = metadata["selector"].get("organization_id", "")
    else:
        if not state["services"]["api"]["organization_id"]:
            logger.error(
                "Selector verification failed: please ensure the 'selector' field is correct: %s",
                metadata.get("selector"),
            )
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    solution_svc = SolutionService(keycloak_token=keycloak_token, spec=spec, state=state["services"])
    if not state["services"]["api"]["solution_id"]:
        logger.info("[api] Creating solution")
        response = solution_svc.create()
        if response is None:
            return CommandResponse.fail()
        solution = response.json()
        logger.info(json.dumps(solution, indent=2))
        logger.info(f"Solution {solution['id']} successfully created")
    else:
        logger.info(f"[api] Updating solution {state['services']['api']['solution_id']}")
        response = solution_svc.update()
        if response is None:
            return CommandResponse.fail()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = solution_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        solution = response_json
        logger.info(json.dumps(solution, indent=2))
        logger.info(f"[api] Solution {solution['id']} successfully updated")
    state["services"]["api"]["solution_id"] = solution.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    # update run_templates
    sidecars = content.get("spec").get("sidecars", {})
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
    if not solution.get("id"):
        sys.exit(1)
