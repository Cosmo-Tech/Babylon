import unittest
from Babylon.utils.environment import Environment

env = Environment()


class OrganizationServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    # @mock.patch.object(OrganizationService, 'create')
    # def test_create(self, organizationservice_create):
    #     the_response = Response()
    #     the_response.status_code = 201
    #     the_response._content = b'{"id" : "1", "name": "My Organization"}'
    #     organizationservice_create.return_value = the_response
    #     payload = str(env.pwd / "Babylon/tests/api/organizations/payload.json")
    #     result = CliRunner().invoke(create, [payload], standalone_mode=False)
    #     states = env.get_state_from_local()
    #     assert states["services"]["api"]["organization_id"] == '1'

    # @mock.patch.object(OrganizationService, 'get')
    # def test_get(self, organizationservice_get):
    #     the_response = Response()
    #     the_response.status_code = 201
    #     the_response._content = b'{"id" : "1", "name": "My Organization"}'
    #     organizationservice_get.return_value = the_response

    #     result = CliRunner().invoke(get, standalone_mode=False)
    #     states = env.get_state_from_local()
    #     assert states["services"]["api"]["organization_id"] == '1'


if __name__ == "__main__":
    unittest.main()
