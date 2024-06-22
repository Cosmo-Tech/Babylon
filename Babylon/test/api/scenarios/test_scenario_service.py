import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.scenarios.services.scenario_api_svc import ScenarioService
from Babylon.commands.api.scenarios.get_all import get_all
from Babylon.commands.api.scenarios.get import get
from Babylon.commands.api.scenarios.update import update
from Babylon.commands.api.scenarios.delete import delete
from Babylon.commands.api.scenarios.create import create
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class ScenarioServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch.object(ScenarioService, 'get_all')
    def test_get_all(self, mock_get_all):
        the_response = Response()
        the_response._content = b'[{"id": "1", "name": "Scenario 1"}, {"id" : "2", "name": "Scenario 2"}]'
        mock_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["--organization-id", "1", "--workspace-id", "1"], standalone_mode=False)

        assert len(result.return_value.data) == 2

    @mock.patch.object(ScenarioService, 'get')
    def test_get(self, mock_get):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "Scenario"}'
        mock_get.return_value = the_response

        result = CliRunner().invoke(get, ["--organization-id", "1", "--workspace-id", "1", "--scenario-id", "1"],
                                    standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "Scenario"}

    @mock.patch.object(ScenarioService, 'update')
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

    @mock.patch.object(ScenarioService, 'delete')
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code": "204", "descripton": "Successfull"}'
        mock_delete.return_value = the_response
        CliRunner().invoke(delete, ["--organization-id", "1", "--workspace-id", "1", "--scenario-id", "1"],
                           standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["scenario_id"] == ""

    @mock.patch.object(ScenarioService, 'create')
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
