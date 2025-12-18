from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.organization_security import OrganizationSecurity
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest

from Babylon.commands.api.client import get_organization_api_instance
from Babylon.commands.macro.deploy import update_object_security
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
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    api_section = state["services"]["api"]
    api_section["organization_id"] = payload.get("id") or api_section.get("organization_id", "")
    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    api_instance = get_organization_api_instance(config=config, keycloak_token=keycloak_token)

    if not api_section["organization_id"]:
        logger.info("Creating organization")
        organization_create_request = OrganizationCreateRequest.from_dict(payload)
        organization = api_instance.create_organization(organization_create_request)
        if organization is None:
            return CommandResponse.fail()
        logger.info(f"Organization {organization.id} successfully created")
        state["services"]["api"]["organization_id"] = organization.id
    else:
        logger.info(f"Updating organization {api_section['organization_id']}")
        organization_update_request = OrganizationUpdateRequest.from_dict(payload)
        updated = api_instance.update_organization(
            organization_id=api_section["organization_id"], organization_update_request=organization_update_request
        )
        if updated is None:
            return CommandResponse.fail()
        if payload.get("security"):
            try:
                current_security = api_instance.get_organization_security(
                    organization_id=api_section["organization_id"]
                )
                update_object_security(
                    "organization",
                    current_security=current_security,
                    desired_security=OrganizationSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=api_section["organization_id"],
                )
            except Exception as e:
                logger.error(f"Failed to update organization security: {e}")
                return CommandResponse.fail()
        logger.info(f"Organization {api_section['organization_id']} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
