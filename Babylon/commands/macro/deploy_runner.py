import os
import sys

from json import dumps
from logging import getLogger

from click import echo, style

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_runner(file_content: str):
    _ret = [""]
    _ret.append("Runner deployment")
    _ret.append("")
    echo(style("\n".join(_ret), bold=True, fg="green"))
    config, state = env.retrieve_config_state_func()
    content = env.fill_template(data=file_content, state=state)
    api_section = state["services"]["api"]
    keycloak_token = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    api_section["runner_id"] = (payload.get("id") or api_section["runner_id"])
    spec = dict()
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    runner_service = RunnerService(keycloak_token=keycloak_token, spec=spec, config=config, state=api_section)
    sidecars = content.get("spec").get("sidecars", {})
    if not api_section["runner_id"]:
        logger.info("Creating runner")
        response = runner_service.create()
        if response is None:
            return CommandResponse.fail()
        runner = response.json()
        logger.info(f"Runner {[runner['id']]} successfully created")
        state["services"]["api"]["runner_id"] = runner.get("id")
    else:
        logger.info(f"Updating runner {[api_section['runner_id']]}")
        response = runner_service.update()
        if response is None:
            return CommandResponse.fail()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = runner_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        runner = response_json
        logger.info(f"Runner {[runner['id']]} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    if sidecars:
        run_scripts = sidecars.get("run_scripts")
        if run_scripts:
            data = run_scripts.get("post_deploy.sh", "")
            if data:
                os.system(data)
        if not runner.get("id"):
            sys.exit(1)
