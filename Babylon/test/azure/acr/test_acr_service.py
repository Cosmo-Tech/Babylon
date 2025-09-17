import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.azure.acr.delete import delete
from Babylon.commands.azure.acr.list import list
from Babylon.commands.azure.acr.pull import pull
from Babylon.commands.azure.acr.push import push
from Babylon.utils.environment import Environment

env = Environment()


class AzureContainerRegistryServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = False

    @mock.patch('azure.containerregistry.ContainerRegistryClient.get_manifest_properties')
    @mock.patch('azure.containerregistry.ContainerRegistryClient.delete_manifest')
    def test_delete(self, mock_get_manifest_properties, mock_delete_manifest):
        result = CliRunner().invoke(delete, ["--image", "hello-world:latest"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('azure.containerregistry.ContainerRegistryClient.list_repository_names')
    @mock.patch('azure.containerregistry.ContainerRegistryClient.list_tag_properties')
    def test_list(self, mock_list_repository_names, mock_list_tag_properties):
        result = CliRunner().invoke(list, standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('docker.client.ImageCollection.pull')
    @mock.patch('docker.client.ImageCollection.remove')
    def test_pull(self, mock_pull, mock_remove):
        result = CliRunner().invoke(pull, ["--image", "hello-world:latest"], standalone_mode=False)

        assert result.return_value.status_code == 0

    @mock.patch('docker.client.ImageCollection.push')
    @mock.patch('docker.client.ImageCollection.get')
    @mock.patch('docker.client.ImageCollection.remove')
    def test_push(self, mock_push, mock_get, mock_remove):
        result = CliRunner().invoke(push, ["--image", "hello-world:latest"], standalone_mode=False)

        assert result.return_value.status_code == 0


if __name__ == "__main__":
    unittest.main()
