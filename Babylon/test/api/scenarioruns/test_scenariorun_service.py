import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.scenarioruns.services.api import ScenarioRunService
from Babylon.commands.api.scenarioruns.cumulated_logs import cumulated_logs
from Babylon.commands.api.scenarioruns.logs import logs
from Babylon.commands.api.scenarioruns.status import status
from Babylon.commands.api.scenarioruns.stop import stop
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class ScenarioRunServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch.object(ScenarioRunService, 'cumulated_logs')
    def test_cumulated_logs(self, mock_cumulated_logs):
        the_response = Response()
        the_response._content = b'{"logs": "Cumulated logs"}'
        mock_cumulated_logs.return_value = the_response

        result = CliRunner().invoke(cumulated_logs, ["--organization-id", "1", "--scenariorun-id", "1"],
                                    standalone_mode=False)

        assert result.return_value.data == {"logs": "Cumulated logs"}

    @mock.patch.object(ScenarioRunService, 'logs')
    def test_logs(self, mock_logs):
        the_response = Response()
        the_response._content = b'{"logs": "A lot of logs"}'
        mock_logs.return_value = the_response

        result = CliRunner().invoke(logs, ["--organization-id", "1", "--scenariorun-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"logs": "A lot of logs"}

    @mock.patch.object(ScenarioRunService, 'status')
    def test_status(self, mock_status):
        the_response = Response()
        the_response._content = b'{"phase": "Succeeded"}'
        mock_status.return_value = the_response

        result = CliRunner().invoke(status, ["--organization-id", "1", "--scenariorun-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"phase": "Succeeded"}

    @mock.patch.object(ScenarioRunService, 'stop')
    def test_stop(self, mock_stop):
        the_response = Response()
        the_response._content = b'{"phase": "Failed"}'
        mock_stop.return_value = the_response

        result = CliRunner().invoke(stop, ["--organization-id", "1", "--scenariorun-id", "1"], standalone_mode=False)

        assert result.return_value.data == {"phase": "Failed"}


if __name__ == "__main__":
    unittest.main()
