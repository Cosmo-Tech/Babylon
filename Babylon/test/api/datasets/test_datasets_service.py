import unittest
from unittest import mock
from click.testing import CliRunner
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.commands.api.datasets.get import get
from Babylon.commands.api.datasets.get_all import get_all
from Babylon.commands.api.datasets.delete import delete
from Babylon.commands.api.datasets.search import search
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class DatasetServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()
        env.remote = False

    @mock.patch.object(DatasetService, "get")
    def test_get(self, datasetservice_get):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Dataset"}'
        datasetservice_get.return_value = the_response

        result = CliRunner().invoke(
            get,
            ["--organization-id", "my_organization_id", "--dataset-id", "1"],
            standalone_mode=False,
        )
        assert result.return_value.data == {"id": "1", "name": "Dataset"}

    @mock.patch.object(DatasetService, "get_all")
    def test_get_all(self, datasetservice_get_all):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'[{"id": "1", "name": "Dataset"}, {"id" : "2", "name": "Dataset2"}]'
        datasetservice_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["--organization-id", "my_organization_id"], standalone_mode=False)
        assert len(result.return_value.data) == 2

    @mock.patch.object(DatasetService, "delete")
    def test_delete(self, datasetservice_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code" : "204", "description": "Request successful"}'
        datasetservice_delete.return_value = the_response

        CliRunner().invoke(
            delete,
            ["--organization-id", "my_organization_id", "--dataset-id", "1"],
            standalone_mode=False,
        )

        states = env.get_state_from_local()
        assert states["services"]["api"]["dataset_id"] == ""

    @mock.patch.object(DatasetService, "search")
    def test_search(self, datasetservice_search):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "Dataset"}'
        datasetservice_search.return_value = the_response

        result = CliRunner().invoke(
            search,
            ["--organization-id", "my_organization_id", "atag"],
            standalone_mode=False,
        )

        assert result.return_value.data == {"id": "1", "name": "Dataset"}


if __name__ == "__main__":
    unittest.main()
