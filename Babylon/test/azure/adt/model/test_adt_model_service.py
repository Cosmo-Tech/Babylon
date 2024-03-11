import mock
import unittest
from click.testing import CliRunner
from Babylon.commands.azure.adt.model.get_all import get_all
from Babylon.commands.azure.adt.model.upload import upload
from Babylon.utils.environment import Environment

env = Environment()


class AzureDigitalTwinsModelServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch('azure.digitaltwins.core.DigitalTwinsClient.list_models')
    def test_create(self, mock_list_models):
        result = CliRunner().invoke(get_all, standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('azure.digitaltwins.core.DigitalTwinsClient.create_models')
    @mock.patch('azure.digitaltwins.core.DigitalTwinsClient.delete_model')
    @mock.patch('azure.digitaltwins.core.DigitalTwinsClient.get_model')
    def test_upload(self, mock_dt_client_create_models, mock_dt_client_delete_model, mock_dt_client_get_model):
        model_folder = str(env.pwd / "Babylon/test/azure/adt/model")
        result = CliRunner().invoke(upload, [model_folder], standalone_mode=False)

        assert result.return_value.status_code == 0


if __name__ == "__main__":
    unittest.main()
