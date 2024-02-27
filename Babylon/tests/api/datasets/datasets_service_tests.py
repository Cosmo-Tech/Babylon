import mock
import unittest
from click.testing import CliRunner
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.api.datasets.create import create
from Babylon.commands.api.datasets.get import get
from Babylon.commands.api.datasets.get_all import get_all
from Babylon.commands.api.datasets.delete import delete
from Babylon.commands.api.datasets.search import search
from Babylon.commands.api.datasets.update import update
from Babylon.utils.environment import Environment
from requests.models import Response

env = Environment()


class DatasetServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    @mock.patch.object(DatasetService, 'create')
    @mock.patch.object(DatasetService, 'get_status')
    @mock.patch.object(DatasetService, 'link_to_workspace')
    @mock.patch.object(DatasetService, 'refresh')
    def test_create(self, mock_create, mock_get_status, mock_link_to_workspace, mock_refresh):
        create_response = Response()
        create_response.status_code = 201
        create_response._content = b'{"id" : "1", "name": "ADT Dataset"}'
        mock_create.return_value = create_response

        # getstatus_response = Response()
        # getstatus_response._content = b'{"success"}'
        # mock_get_status.return_value = getstatus_response

        # link_to_workspace_response = Response()
        # link_to_workspace_response._content = b'{"id" : "1", "name": "ADT Dataset"}'
        # mock_link_to_workspace.return_value = link_to_workspace_response

        # refresh_response = Response()
        # refresh_response._content = b'{"successful"}'
        # mock_refresh.return_value = refresh_response

        result = CliRunner().invoke(
            create,
            ["--organization-id", "my_organization_id",
             str(env.pwd / "Babylon/tests/api/datasets/payload.json")],
            standalone_mode=False)

        assert result.exit_code == 0

    @mock.patch.object(DatasetService, 'get')
    def test_get(self, datasetservice_get):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "ADT Dataset"}'
        datasetservice_get.return_value = the_response

        result = CliRunner().invoke(get, ["--organization-id", "my_organization_id", "--dataset-id", "1"],
                                    standalone_mode=False)
        assert result.return_value.data == {"id": "1", "name": "ADT Dataset"}

    @mock.patch.object(DatasetService, 'get_all')
    def test_get_all(self, datasetservice_get_all):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'[{"id": "1", "name": "ADT Dataset"}, {"id" : "2", "name": "ADT Dataset2"}]'
        datasetservice_get_all.return_value = the_response

        result = CliRunner().invoke(get_all, ["--organization-id", "my_organization_id"], standalone_mode=False)
        assert len(result.return_value.data) == 2

    @mock.patch.object(DatasetService, 'delete')
    def test_delete(self, datasetservice_delete):
        the_response = Response()
        the_response.status_code = 204
        the_response._content = b'{"code" : "204", "description": "Request successful"}'
        datasetservice_delete.return_value = the_response

        CliRunner().invoke(delete, ["--organization-id", "my_organization_id", "--dataset-id", "1"],
                           standalone_mode=False)

        states = env.get_state_from_local()
        assert states["services"]["api"]["dataset.storage_id"] == ""

    @mock.patch.object(DatasetService, 'search')
    def test_search(self, datasetservice_search):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "ADT Dataset"}'
        datasetservice_search.return_value = the_response

        result = CliRunner().invoke(search, ["--organization-id", "my_organization_id", "atag"], standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "ADT Dataset"}

    @mock.patch.object(DatasetService, 'update')
    def test_update(self, datasetservice_update):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"id": "1", "name": "ADT Dataset"}'
        datasetservice_update.return_value = the_response
        payload_file = str(env.pwd / "Babylon/tests/api/datasets/payload.json")
        result = CliRunner().invoke(update,
                                    ["--organization-id", "my_organization_id", "--dataset-id", "1", payload_file],
                                    standalone_mode=False)

        assert result.return_value.data == {"id": "1", "name": "ADT Dataset"}


if __name__ == "__main__":
    unittest.main()
