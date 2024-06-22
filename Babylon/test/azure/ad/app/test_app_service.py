import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.azure.ad.app.create import create
from Babylon.commands.azure.ad.app.delete import delete
from Babylon.commands.azure.ad.app.get_all import get_all
from Babylon.commands.azure.ad.app.get import get
from Babylon.commands.azure.ad.app.update import update
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class AzureDirectoyAppServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch('polling2.poll')
    def test_create(self, mock_poll):
        registration_file = str(env.pwd / "Babylon/test/azure/ad/app/registration_file.json")
        result = CliRunner().invoke(create, ["--file", registration_file], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('polling2.poll')
    def test_delete(self, mock_poll):
        result = CliRunner().invoke(delete, ["my-object-id"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.get')
    def test_get_all(self, mock_get):
        the_response = Response()
        the_response.status_code = 0
        the_response._content = b'{"value": "my-response"}'
        mock_get.return_value = the_response
        result = CliRunner().invoke(get_all, standalone_mode=False)

        assert result.output == "'my-response'\n"

    @mock.patch('polling2.poll')
    def test_get(self, mock_poll):
        result = CliRunner().invoke(get, ["my-object-id"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.patch')
    def test_update(self, mock_patch):
        the_response = Response()
        the_response.status_code = 0
        mock_patch.return_value = the_response
        registration_file = str(env.pwd / "Babylon/test/azure/ad/app/registration_file.json")
        result = CliRunner().invoke(update, ["--file", registration_file, "my-object-id"], standalone_mode=False)

        assert result.return_value.status_code == 0


if __name__ == "__main__":
    unittest.main()
