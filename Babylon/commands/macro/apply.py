import sys
import yaml
# import json
import pathlib

from logging import getLogger
from flatten_json import flatten
from mako.template import Template
from click import Path, argument, command
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.utils.environment import Environment
# from Babylon.utils.yaml_utils import yaml_to_json
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
    # payload_json = yaml_to_json(payload)
    # payload_dict: dict = json.loads(payload_json)
    match kind:
        case "Workspace":
            deploy_workspace(payload, deploy_dir)
        case "Solution":
            deploy_solution(payload, deploy_dir)
        case "Organization":
            result = content.replace("{{", "${").replace("}}", "}")
            t = Template(text=result, strict_undefined=True)
            values_file = pathlib.Path().cwd() / "variables.yaml"
            vars = dict()
            if values_file.exists():
                vars = yaml.safe_load(values_file.open())
            state = env.retrieve_state_func()
            flattenstate = flatten(state.get("services"), separator=".")
            payload = t.render(**vars, services=flattenstate)
            deploy_organization(payload)
    files.pop()
    iter_files_to_deploy(files=files, deploy_dir=deploy_dir)
