import os
import unittest
from pathlib import Path
from click.testing import CliRunner
from ruamel.yaml import YAML
from Babylon.commands.azure.arm.create import create
from Babylon.utils.environment import Environment
from Babylon.utils import BABYLON_PATH

env = Environment()


class AzureAppInsightServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
        env.get_namespace_from_local()

    def test_create(self):
        CliRunner().invoke(create, ["my-deployment-name", "--template-uri", "https://my-template-uri"],
                           standalone_mode=False)
        deployment_file = Path(os.path.join(BABYLON_PATH, "..", "my-deployment-name.yaml"))
        assert deployment_file.exists()

        with open(deployment_file, mode='r') as file:
            arm_deployment = YAML().load(file)

        assert arm_deployment["deployment_name"] == "my-deployment-name"
        assert arm_deployment["template_uri"] == "https://my-template-uri"

        deployment_file.unlink()


if __name__ == "__main__":
    unittest.main()
