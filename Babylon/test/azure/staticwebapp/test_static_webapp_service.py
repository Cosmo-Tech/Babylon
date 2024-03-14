import mock
import unittest
from click.testing import CliRunner
from Babylon.utils.environment import Environment
from Babylon.commands.azure.staticwebapp.create import create
from Babylon.commands.azure.staticwebapp.delete import delete
from Babylon.commands.azure.staticwebapp.get_all import get_all
from Babylon.commands.azure.staticwebapp.get import get
from Babylon.commands.azure.staticwebapp.update import update
from requests.models import Response

env = Environment()


class AzureAppInsightServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch('requests.put')
    def test_create(self, mock_put):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"name": "my-webapp-name"}'
        mock_put.return_value = the_response
        swa_file = str(env.pwd / "Babylon/test/azure/staticwebapp/swa_file.yaml")
        result = CliRunner().invoke(create, ["my-webapp-name", "--file", swa_file], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.delete')
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"name": "my-webapp-name"}'
        mock_delete.return_value = the_response
        result = CliRunner().invoke(delete, ["-D", "my-webapp-name"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.get')
    def test_get_all(self, mock_get_all):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"value": "my-webapp-name"}'
        mock_get_all.return_value = the_response
        result = CliRunner().invoke(get_all, ["--filter", ""], standalone_mode=False)

        assert result.output == "'my-webapp-name'\n"

    @mock.patch('requests.get')
    def test_get(self, mock_get):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "my-webapp-name"}'
        mock_get.return_value = the_response
        result = CliRunner().invoke(get, ["my-webapp"], standalone_mode=False)

        assert result.output == "{'id': 'my-webapp-name'}\n"

    @mock.patch('requests.put')
    def test_update(self, mock_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "my-webapp-name"}'
        mock_update.return_value = the_response
        swa_file = str(env.pwd / "Babylon/test/azure/staticwebapp/swa_file.yaml")
        result = CliRunner().invoke(update, ["my-webapp", "--file", swa_file], standalone_mode=False)

        assert result.return_value.data == {'id': 'my-webapp-name'}


if __name__ == "__main__":
    unittest.main()
