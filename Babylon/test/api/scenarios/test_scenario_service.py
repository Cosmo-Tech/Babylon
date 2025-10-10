import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.commands.api.runners.get_all import get_all
from Babylon.commands.api.runners.get import get
from Babylon.commands.api.runners.update import update
from Babylon.commands.api.runners.delete import delete
from Babylon.commands.api.runners.create import create
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class ScenarioServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch.object(RunnerService, 'get_all')
    def test_get_all(self, mock_get_all):
        the_response = Response()
        the_response._content = b'[{"id": "1", "name": "Scenario 1"}, {"id" : "2", "name": "Scenario 2"}]'
        mock_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["--organization-id", "1", "--workspace-id", "1"], standalone_mode=False)

        assert len(result.return_value.data) == 2

    @mock.patch.object(RunnerService, 'get')
    def test_get(self, mock_get):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "Scenario"}'
        mock_get.return_value = the_response

        result = CliRunner().invoke(get, ["--organization-id", "1", "--workspace-id", "1", "--scenario-id", "1"],
                                    standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Scenario"}

    @mock.patch.object(RunnerService, 'update')
    def test_update(self, mock_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Scenario updated"}'
        mock_update.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/scenarios/payload.json")
        result = CliRunner().invoke(
            update, ["--organization-id", "1", "--workspace-id", "1", "--scenario-id", "1", payload_file],
            standalone_mode=False)

        assert result.return_value.data.get("name") == 'Scenario updated'

    @mock.patch.object(RunnerService, 'delete')
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code": "204", "descripton": "Successfull"}'
        mock_delete.return_value = the_response
        CliRunner().invoke(delete, ["--organization-id", "1", "--workspace-id", "1", "--scenario-id", "1"],
                           standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["scenario_id"] == ""

    @mock.patch.object(RunnerService, 'create')
    def test_create(self, mock_create):
        the_response = Response()
        the_response.status_code = 201
        the_response._content = b'{"id": "1", "name": "A scenario"}'
        mock_create.return_value = the_response
        payload_file = str(env.pwd / "Babylon/test/api/scenarios/payload.json")
        CliRunner().invoke(create, ["--organization-id", "1", "--workspace-id", "1", payload_file],
                           standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["scenario_id"] == "1"


if __name__ == "__main__":
    unittest.main()
