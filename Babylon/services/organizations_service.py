import sys
import pathlib
from typing import Optional
from logging import getLogger
from posixpath import basename
from Babylon.utils.request import oauth_request
from Babylon.utils.checkers import check_ascii, check_email
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from click import Context

logger = getLogger("Babylon")
env = Environment()


class OrganizationsService:

    def __init__(self, states: dict, azure_token: str, spec: Optional[dict] = None):
        self.states = states
        self.azure_token = azure_token
        self.spec = spec

    def create(self, name: str, security_id: str, security_role: str, org_file: Optional[pathlib.Path] = None):
        security_id = security_id or self.states['azure']['email']
        check_email(security_id)
        check_ascii(name)
        path_file = f"{env.context_id}.{env.environ_id}.organization.yaml"
        org_file = org_file or env.working_dir.payload_path / path_file
        if not org_file.exists():
            logger.error(f"No such file: '{basename(org_file)}' in .payload directory")
            sys.exit(1)

        details = env.fill_template(org_file,
                                    data={
                                        "name": name,
                                        "security_id": security_id,
                                        "security_role": security_role.lower()
                                    })
        url = self.states["api"]["url"]
        return oauth_request(f"{url}/organizations", self.azure_token, type="POST", data=details)

    def delete(self, ctx: Context, id: str, force_validation: bool = False):
        url = self.states["api"]["url"]
        organization_id = self.states["api"]["organization_id"]
        if not id:
            logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
            logger.error(f"Current value: {organization_id}")

        organization_id = id or organization_id
        logger.info(f"You trying to delete the '{organization_id}' organization")
        if not force_validation and not confirm_deletion("organization", organization_id):
            return CommandResponse.fail()
        if not organization_id:
            logger.error("Organization id is missing")
            return CommandResponse.fail()
        return oauth_request(f"{url}/organizations/{organization_id}", self.azure_token, type="DELETE")

    def get(self, ctx: Context):
        url = self.states["api"]["url"]
        organization_id = self.states["api"]["organization_id"]

        if not id:
            logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
            logger.error(f"Current value: {organization_id}")
        organization_id = id or organization_id
        if not organization_id:
            logger.error("Organization id is missing")
            return CommandResponse.fail()

        return oauth_request(f"{url}/organizations/{organization_id}", self.azure_token)

    def get_all(self):
        url = self.states["api"]["url"]
        return oauth_request(f"{url}/organizations", self.azure_token)

    def update(self, id: str, organization_file: Optional[pathlib.Path]):
        url = self.states["api"]["url"]
        organization_id = id or self.states["api"]["organization_id"]
        path_file = f"{env.context_id}.{env.environ_id}.organization.yaml"
        organization_file = organization_file or env.working_dir.payload_path / path_file
        if not organization_file.exists():
            return CommandResponse.fail()
        details = env.fill_template(organization_file)
        return oauth_request(f"{url}/organizations/{organization_id}", self.azure_token, type="PATCH", data=details)
