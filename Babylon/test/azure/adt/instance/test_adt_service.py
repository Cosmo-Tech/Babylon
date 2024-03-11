import mock
import unittest
from click.testing import CliRunner
from Babylon.commands.azure.adt.instance.create import create
from Babylon.commands.azure.adt.instance.delete import delete
from Babylon.commands.azure.adt.instance.get_all import get_all
from Babylon.commands.azure.adt.instance.get import get
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class AzureDigitalTwinsServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch('azure.mgmt.digitaltwins.AzureDigitalTwinsManagementClient.digital_twins')
    @mock.patch(
        'azure.mgmt.authorization._authorization_management_client.AuthorizationManagementClient.role_assignments')
    def test_create(self, mock_digital_twins, mock_role_assignments):
        result = CliRunner().invoke(create, standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('azure.mgmt.digitaltwins.AzureDigitalTwinsManagementClient.digital_twins')
    def test_delete(self, mock_digital_twins):
        result = CliRunner().invoke(delete, ["-D", "my-instance-name"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('azure.mgmt.digitaltwins.AzureDigitalTwinsManagementClient.digital_twins')
    def test_get_all(self, mock_digital_twins):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "my-instance"}, {"id": "2", "name": "my-instance-2}'
        mock_digital_twins.return_value = the_response
        result = CliRunner().invoke(get_all, standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('azure.mgmt.digitaltwins.AzureDigitalTwinsManagementClient.digital_twins')
    def test_get(self, mock_digital_twins):
        the_response = Response()
        the_response._content = b'{"id": "1", "name": "my-instance"}'
        mock_digital_twins.return_value = the_response
        result = CliRunner().invoke(get, ["my-instance-name"], standalone_mode=False)

        assert result.return_value.status_code == 0


if __name__ == "__main__":
    unittest.main()
