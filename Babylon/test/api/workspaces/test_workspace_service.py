import unittest
from unittest import mock

from click.testing import CliRunner
from requests.models import Response

from Babylon.commands.api.workspaces.create import create
from Babylon.commands.api.workspaces.delete import delete
from Babylon.commands.api.workspaces.get import get
from Babylon.commands.api.workspaces.get_all import get_all
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.commands.api.workspaces.update import update
from Babylon.utils.environment import Environment

env = Environment()


class WorkspaceServiceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env.get_namespace_from_local()
        env.remote = False

    @mock.patch.object(WorkspaceService, "create")
    def test_create(self, mock_create):
        the_response = Response()
        the_response.status_code = 201
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_create.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/workspaces/payload.json")
        result = CliRunner().invoke(create, ["1", payload_file], standalone_mode=False)
        assert result.return_value.data.get("name") == "Workspace"

    @mock.patch.object(WorkspaceService, "get")
    def test_get(self, mock_get):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_get.return_value = the_response

        result = CliRunner().invoke(get, ["1", "1"], standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Workspace"}

    @mock.patch.object(WorkspaceService, "get_all")
    def test_get_all(self, mock_get_all):
        the_response = Response()
        the_response._content = b'[{"id": "1", "name": "Workspace 1"}, {"id": "2", "name": "Workspace 2"}]'
        mock_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["1", "1"], standalone_mode=False)
        assert len(result.return_value.data) == 2

    @mock.patch.object(WorkspaceService, "update")
    def test_update(self, mock_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Workspace updated"}'
        mock_update.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/workspaces/payload.json")
        result = CliRunner().invoke(update, ["1", "1", payload_file], standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Workspace updated"}

    @mock.patch.object(WorkspaceService, "delete")
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"id": "1", "name": "Workspace"}'
        mock_delete.return_value = the_response

        result = CliRunner().invoke(delete, ["1", "1"], standalone_mode=False)
        assert result.return_value.data.status_code == 204


if __name__ == "__main__":
    unittest.main()
