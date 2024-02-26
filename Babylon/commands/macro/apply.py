import sys
import yaml
import pathlib

from logging import getLogger
from click import Path, argument, command
from Babylon.commands.macro.deploy_dataset import deploy_dataset
from Babylon.commands.macro.deploy_webapp import deploy_swa
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import injectcontext
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_organization import deploy_organization

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@argument("deploy_dir", type=Path(dir_okay=True, exists=True))
def apply(deploy_dir: pathlib.Path):
    """Macro Apply"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
    files = list(pathlib.Path(deploy_dir).iterdir())
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    iter_files_to_deploy(files_to_deploy, deploy_dir)


def iter_files_to_deploy(files: list[pathlib.Path], deploy_dir: Path):

    if not len(files):
        logger.info("Deployment completed")
        sys.exit(1)
    content = files[-1].open().read()
    payload = yaml.safe_load(content)
    kind = payload.get("kind")
    match kind:
        case "Dataset":
            deploy_dataset(content)
        case "WebApp":
            deploy_swa(content)
        case "Workspace":
            deploy_workspace(content, deploy_dir)
        case "Solution":
            deploy_solution(content, deploy_dir)
        case "Organization":
            deploy_organization(content)
    files.pop()
    iter_files_to_deploy(files=files, deploy_dir=deploy_dir)
