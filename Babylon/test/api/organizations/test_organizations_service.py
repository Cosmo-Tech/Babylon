import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.create import create
from Babylon.commands.api.organizations.delete import delete
from Babylon.commands.api.organizations.get_all import get_all
from Babylon.commands.api.organizations.get import get
from Babylon.commands.api.organizations.update import update
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from requests.models import Response

env = Environment()


class OrganizationServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch.object(OrganizationService, 'create')
    def test_create(self, organizationservice_create):
        the_response = Response()
        the_response.status_code = 201
        the_response._content = b'{"id" : "1", "name": "My Organization"}'
        organizationservice_create.return_value = the_response
        payload = str(env.pwd / "Babylon/test/api/organizations/payload.json")
        CliRunner().invoke(create, [payload], standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["organization_id"] == '1'

    @mock.patch.object(OrganizationService, 'delete')
    def test_delete(self, organizationservice_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code" : "204", "description": "Succeeded"}'
        organizationservice_delete.return_value = the_response

        CliRunner().invoke(delete, ["--organization-id", "my_organization_id"], standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["organization_id"] == ""

    @mock.patch.object(OrganizationService, 'get_all')
    def test_get_all(self, organizationservice_get_all):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'[{"id": "1", "name": "Org 1"}, {"id" : "2", "name": "Org 2"}]'
        organizationservice_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, standalone_mode=False)

        assert len(result.return_value.data) == 2

    @mock.patch.object(OrganizationService, 'get')
    def test_get(self, organizationservice_get):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id" : "1", "name": "My Organization"}'
        organizationservice_get.return_value = the_response

        result = CliRunner().invoke(get, standalone_mode=False)
        assert result.return_value.data == {"id": "1", "name": "My Organization"}

    @mock.patch.object(OrganizationService, 'update')
    def test_update(self, organizationservice_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id" : "1", "name": "My Organization updated"}'
        organizationservice_update.return_value = the_response
        payload = str(env.pwd / "Babylon/test/api/organizations/payload.json")
        result = CliRunner().invoke(update, ["--organization-id", "my_organization_id", payload], standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "My Organization updated"}


if __name__ == "__main__":
    unittest.main()
