# import os
# import sys
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
    state = env.retrieve_state_func()
    api_section = state["services"]["api"]
    content = env.fill_template(data=file_content, state=state)
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    spec = dict()
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    runner_service = RunnerService(keycloak_token=keycloak_token, spec=spec, config=config, state=api_section)
    # sidecars = content.get("spec").get("sidecars", {})
    if not payload.get("id"):
        logger.info("Creating runner")
        response = runner_service.create()
        if response is None:
            return CommandResponse.fail()
        runner = response.json()
        logger.info(f"Runner {[runner['id']]} successfully created")
    # For this moment the apply just for create not fo update !!!!!

    # else:
    #     logger.info(f"Updating runner {[payload.get("id")]}")
    #     response = runner_service.update()
    #     if response is None:
    #         return CommandResponse.fail()
    #     response_json = response.json()
    #     old_security = response_json.get("security")
    #     security_spec = runner_service.update_security(old_security=old_security)
    #     response_json["security"] = security_spec
    #     runner = response_json
    #     logger.info(f"Runner {[runner['id']]} successfully updated")
    # if sidecars:
    #     run_scripts = sidecars.get("run_scripts")
    #     if run_scripts:
    #         data = run_scripts.get("post_deploy.sh", "")
    #         if data:
    #             os.system(data)
    #     if not runner.get("id"):
    #         sys.exit(1)
    return runner.get("id")