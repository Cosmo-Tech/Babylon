import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.commands.api.runs.logs import logs
from Babylon.commands.api.runs.status import status
from Babylon.commands.api.runs.stop import stop
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class RunServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = False

    @mock.patch.object(RunService, 'logs')
    def test_logs(self, mock_logs):
        the_response = Response()
        the_response._content = b'{"logs": "A lot of logs"}'
        mock_logs.return_value = the_response

        result = CliRunner().invoke(logs, ["--organization-id", "1", "--run-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"logs": "A lot of logs"}

    @mock.patch.object(RunService, 'status')
    def test_status(self, mock_status):
        the_response = Response()
        the_response._content = b'{"phase": "Succeeded"}'
        mock_status.return_value = the_response

        result = CliRunner().invoke(status, ["--organization-id", "1", "--run-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"phase": "Succeeded"}

    @mock.patch.object(RunService, 'stop')
    def test_stop(self, mock_stop):
        the_response = Response()
        the_response._content = b'{"phase": "Failed"}'
        mock_stop.return_value = the_response

        result = CliRunner().invoke(stop, ["--organization-id", "1", "--run-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"phase": "Failed"}


if __name__ == "__main__":
    unittest.main()
