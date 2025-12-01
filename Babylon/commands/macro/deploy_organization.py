import os
import sys
from json import dumps
from logging import getLogger

from click import echo, style

from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_organization(namespace: str, file_content: str):
    _ret = [""]
    _ret.append("Organization deployment")
    _ret.append("")
    echo(style("\n".join(_ret), bold=True, fg="green"))
    env.get_ns_from_text(content=namespace)
    config, state = env.retrieve_config_state_func()
    content = env.fill_template(data=file_content, state=state)
    keycloak_token = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    api_section = state["services"]["api"]
    api_section["organization_id"] = payload.get("id") or api_section.get("organization_id", "")
    spec = dict()
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    organization_service = OrganizationService(
        keycloak_token=keycloak_token, spec=spec, config=config, state=api_section
    )
    sidecars = content.get("spec").get("sidecars", {})
    if not api_section["organization_id"]:
        logger.info("Creating organization")
        response = organization_service.create()
        if response is None:
            return CommandResponse.fail()
        organization = response.json()
        logger.info(f"Organization {[organization['id']]} successfully created")
        state["services"]["api"]["organization_id"] = organization.get("id")
    else:
        logger.info(f"Updating organization {[api_section['organization_id']]}")
        response = organization_service.update()
        if response is None:
            return CommandResponse.fail()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
        logger.info(f"Organization {[organization['id']]} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    if sidecars:
        run_scripts = sidecars.get("run_scripts")
        if run_scripts:
            data = run_scripts.get("post_deploy.sh", "")
            if data:
                os.system(data)
        if not organization.get("id"):
            sys.exit(1)
