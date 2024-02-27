import yaml
import pathlib

from logging import getLogger
from click import Path, argument, command
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import injectcontext
from Babylon.commands.macro.deploy_webapp import deploy_swa
from Babylon.commands.macro.deploy_dataset import deploy_dataset
from Babylon.commands.macro.deploy_workspace import deploy_workspace
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
    kinds = [{'path': f, 'kind': yaml.safe_load(f.open().readline().strip())['kind']} for f in files_to_deploy]

    organizations = list(filter(lambda x: x.get('kind') == "Organization", kinds))
    solutions = list(filter(lambda x: x.get('kind') == "Solution", kinds))
    workspaces = list(filter(lambda x: x.get('kind') == "Workspace", kinds))
    webapps = list(filter(lambda x: x.get('kind') == "WebApp", kinds))
    datasets = list(filter(lambda x: x.get('kind') == "Dataset", kinds))

    for o in organizations:
        p = pathlib.Path(o.get('path'))
        content = p.open().read()
        deploy_organization(content)

    for s in solutions:
        p = pathlib.Path(s.get('path'))
        content = p.open().read()
        deploy_solution(content, deploy_dir)

    for w in workspaces:
        p = pathlib.Path(w.get('path'))
        content = p.open().read()
        deploy_workspace(content, deploy_dir)

    for swa in webapps:
        p = pathlib.Path(swa.get('path'))
        content = p.open().read()
        deploy_swa(content)

    for d in datasets:
        p = pathlib.Path(d.get('path'))
        content = p.open().read()
        deploy_dataset(content)
