import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.commands.api.workspaces.get import get
from Babylon.commands.api.workspaces.get_all import get_all
from Babylon.commands.api.workspaces.update import update
from Babylon.commands.api.workspaces.delete import delete
from Babylon.commands.api.workspaces.create import create
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class SolutionServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch.object(WorkspaceService, 'create')
    def test_create(self, mock_create):
        the_response = Response()
        the_response.status_code = 201
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_create.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/workspaces/payload.json")
        CliRunner().invoke(create, ["--organization-id", "1", payload_file], standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["workspace_id"] == "1"

    @mock.patch.object(WorkspaceService, 'get')
    def test_get(self, mock_get):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_get.return_value = the_response

        result = CliRunner().invoke(get, ["--organization-id", "1", "--workspace-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Workspace"}

    @mock.patch.object(WorkspaceService, 'get_all')
    def test_get_all(self, mock_get_all):
        the_response = Response()
        the_response._content = b'[{"id": "1", "name": "Workspace 1"}, {"id": "2", "name": "Workspace 2"}]'
        mock_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["--organization-id", "1"], standalone_mode=False)

        assert len(result.return_value.data) == 2

    @mock.patch.object(WorkspaceService, 'update')
    def test_update(self, mock_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Workspace updated"}'
        mock_update.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/workspaces/payload.json")
        result = CliRunner().invoke(update, ["--organization-id", "1", "--workspace-id", "1", payload_file],
                                    standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Workspace updated"}

    @mock.patch.object(WorkspaceService, 'delete')
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_delete.return_value = the_response

        CliRunner().invoke(delete, ["--organization-id", "1", "--workspace-id", "1"], standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["workspace_id"] == ""


if __name__ == "__main__":
    unittest.main()
