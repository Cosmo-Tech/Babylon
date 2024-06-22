import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.azure.appinsight.create import create
from Babylon.commands.azure.appinsight.delete import delete
from Babylon.commands.azure.appinsight.get_all import get_all
from Babylon.commands.azure.appinsight.get import get
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class AzureAppInsightServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = True

    @mock.patch('requests.put')
    def test_create(self, mock_put):
        the_response = Response()
        the_response.status_code = 0
        the_response._content = b'{"id": "my-appinsight"}'
        mock_put.return_value = the_response
        app_insigth_file = str(env.pwd / "Babylon/test/azure/appinsight/app_insight_desc.json")
        result = CliRunner().invoke(create, ["my-appinsight", "--file", app_insigth_file], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.delete')
    def test_delete(self, mock_delete):
        the_response = Response()
        the_response.status_code = 0
        mock_delete.return_value = the_response
        result = CliRunner().invoke(delete, ["-D", "my-insight-name"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.get')
    def test_get_all(self, mock_get):
        the_response = Response()
        the_response.status_code = 0
        the_response._content = b'{"value": "my-appinsight"}'
        mock_get.return_value = the_response
        result = CliRunner().invoke(get_all, standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('requests.get')
    def test_get(self, mock_get):
        the_response = Response()
        the_response.status_code = 0
        the_response._content = b'{"value": "my-appinsight"}'
        mock_get.return_value = the_response
        result = CliRunner().invoke(get, ["my-insight-name"], standalone_mode=False)

        assert result.return_value.status_code == 0


if __name__ == "__main__":
    unittest.main()
