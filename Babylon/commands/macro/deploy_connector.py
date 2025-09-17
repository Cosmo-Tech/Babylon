import sys
import json

from logging import getLogger

import click
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token, get_keycloak_token, correct_auth_method
from Babylon.commands.api.connectors.services.connectors_svc import ConnectorService

logger = getLogger("Babylon")
env = Environment()


def deploy_connector(namespace: str, file_content: str):
    _ret = [""]
    _ret.append("Connector deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url = env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func(state_id=env.state_id)
    state["services"]["api"]["url"] = platform_url
    state['services']['azure']['tenant_id'] = env.tenant_id
    content = env.fill_template(data=file_content, state=state)
    auth_method = str(content.get("namespace", {}).get("auth", "azure")).lower()
    auth_method = correct_auth_method(auth_method)
    if auth_method == "azure":
        azure_token = get_azure_token("csm_api")
    else:
        azure_token = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    state["services"]["api"]["connector.storage_id"] = (payload.get("id") 
                                                        or state["services"]["api"]["connector.storage_id"])
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    connector_service = ConnectorService(azure_token=azure_token, spec=spec, state=state["services"])
    if not state["services"]["api"]["connector.storage_id"]:
        logger.info("[api] creating connector storage")
        response = connector_service.create()
        connector = response.json()
        if not connector.get("id"):
            logger.error("[api] Connector storage not created!")
            sys.exit(1)
        else:
            logger.info(f"[api] connector storage {connector['id']} successfully created")
            state["services"]["api"]["connector.storage_id"] = connector.get("id")
            logger.info(json.dumps(connector, indent=2))
    else:
        connector_storage_id = state["services"]["api"]["connector.storage_id"]
        logger.info(f"[api] connector storage {connector_storage_id} already created")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
