import mock
import unittest
from click.testing import CliRunner
from Babylon.commands.api.connectors.service.api import ConnectorService
from Babylon.commands.api.connectors.create import create
from Babylon.commands.api.connectors.get import get
from Babylon.commands.api.connectors.get_all import get_all
from Babylon.commands.api.connectors.delete import delete
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class ConnectorServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch.object(ConnectorService, 'create')
    def test_create(self, connectorservice_create):
        the_response = Response()
        the_response._content = b'{"id" : "1", "name": "ADT Connector"}'
        connectorservice_create.return_value = the_response

        runner = CliRunner()
        runner.invoke(create, [str(env.pwd / "Babylon/test/api/connectors/payload.json")], standalone_mode=False)
        states = env.get_state_from_local()
        assert states["services"]["api"]["connector_id"] == '1'

    @mock.patch.object(ConnectorService, 'get')
    def test_get(self, connectorservice_get):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "ADT Connector"}'
        connectorservice_get.return_value = the_response

        result = CliRunner().invoke(get, ["--connector-id", "1"], standalone_mode=False)
        assert result.return_value.data == {"id": "1", "name": "ADT Connector"}

    @mock.patch.object(ConnectorService, 'get_all')
    def test_get_all(self, connectorservice_get_all):
        the_response = Response()
        the_response._content = b'[{"id": "1", "name": "ADT Connector"}, {"id" : "1", "name": "ADT Connector"}]'
        connectorservice_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, standalone_mode=False)
        assert len(result.return_value.data) == 2

    @mock.patch.object(ConnectorService, 'delete')
    def test_delete(self, connectorservice_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code" : "204", "description": "Request successful"}'
        connectorservice_delete.return_value = the_response

        CliRunner().invoke(delete, ["--connector-id", "1"], standalone_mode=False)

        states = env.get_state_from_local()
        assert states["services"]["api"]["connector_id"] == ""


if __name__ == "__main__":
    unittest.main()
