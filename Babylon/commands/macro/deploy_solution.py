import os
import json
import pathlib

from zipfile import ZipFile
from logging import getLogger
from posixpath import basename
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.solutions.handler.service.api import SolutionHandleService

logger = getLogger("Babylon")
env = Environment()


def deploy_solution(file_content: str, deploy_dir: pathlib.Path) -> bool:
    print("Solution deployment")
    state = env.retrieve_state_func()
    azure_token = get_azure_token("csm_api")
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    service_state = state["services"]
    service_state["api"]["organization_id"] = "o-2v54kow7wvz6"
    service_state["api"]["solution_id"] = (
        payload.get("id") or service_state["api"]["solution_id"]
    )
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    solution_svc = SolutionService(
        azure_token=azure_token, spec=spec, state=service_state
    )
    if not service_state["api"]["solution_id"]:
        response = solution_svc.create()
        solution = response.json()
    else:
        response = solution_svc.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = solution_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        solution = response_json
        logger.info(solution)
    state["services"]["api"]["solution_id"] = solution.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)

    # update run_templates
    sidecars = file_content.get("spec")["sidecars"]
    run_templates = sidecars["azure"]["run_templates"]
    for run_item in run_templates:
        run_id = run_item.get("id")
        for handler_id, deploy in run_item.get("handlers").items():
            if deploy:
                run_id_dir_path: pathlib.Path = pathlib.Path(deploy_dir) / "run_templates" / run_id / handler_id
                solution_handler_svc = SolutionHandleService(
                    azure_token=azure_token, state=state["services"]
                )
                if run_id_dir_path.is_dir():
                    with ZipFile(run_id_dir_path / f"{handler_id}.zip", 'w') as zip_object:
                        for f in run_id_dir_path.iterdir():
                            if basename(f) != f"{handler_id}.zip": 
                                zip_object.write(f, basename(f))
                handler_zip_path = run_id_dir_path / f"{handler_id}.zip"
                solution_handler_svc.upload(
                    run_template_id=run_id,
                    handler_id=handler_id,
                    handler_path=handler_zip_path,
                    override=True,
                )
                os.remove(handler_zip_path)
    return solution.get("id") != ""
