import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.commands.api.runs.logs import logs
from Babylon.commands.api.runs.status import status
from Babylon.commands.api.runs.get import get
from Babylon.commands.api.runs.get_all import get_all
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class RunServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = False

    @mock.patch.object(RunService, 'get')
    def test_get(self, mock_status):
        the_response = Response()
        the_response._content = b'{"id": "1"}'
        mock_status.return_value = the_response

        result = CliRunner().invoke(
            get, ["--organization-id", "1", "--workspace-id", "1", "--runner-id", "1", "--run-id", "1"],
            standalone_mode=False)
        assert result.return_value.data == {"id": "1"}

    @mock.patch.object(RunService, 'get_all')
    def test_get_all(self, mock_status):
        the_response = Response()
        the_response._content = b'[{"id": "1"}, {"id" : "2"}]'
        mock_status.return_value = the_response

        result = CliRunner().invoke(
            get_all, ["--organization-id", "1", "--workspace-id", "1", "--runner-id", "1", "--run-id", "1"],
            standalone_mode=False)
        assert len(result.return_value.data) == 2

    @mock.patch.object(RunService, 'logs')
    def test_logs(self, mock_logs):
        the_response = Response()
        the_response._content = b'{"logs": "A lot of logs"}'
        mock_logs.return_value = the_response

        result = CliRunner().invoke(
            logs, ["--organization-id", "1", "--workspace-id", "1", "--runner-id", "1", "--run-id", "1"],
            standalone_mode=False)
        assert result.return_value.data == {"logs": "A lot of logs"}

    @mock.patch.object(RunService, 'status')
    def test_status(self, mock_status):
        the_response = Response()
        the_response._content = b'{"phase": "Succeeded"}'
        mock_status.return_value = the_response

        result = CliRunner().invoke(
            status, ["--organization-id", "1", "--workspace-id", "1", "--runner-id", "1", "--run-id", "1"],
            standalone_mode=False)
        assert result.return_value.data == {"phase": "Succeeded"}


if __name__ == "__main__":
    unittest.main()
