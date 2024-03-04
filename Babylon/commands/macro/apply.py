import yaml
import pathlib

from logging import getLogger
from click import Path, argument, command
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
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
    heads = []
    for f in files_to_deploy:
        head_ = dict()
        with open(f) as input_file:
            heads_list = [next(input_file) for _ in range(7)]
            head_text = "".join(heads_list)
            head = yaml.safe_load(head_text)
            head_['kind'] = head.get('kind')
            head_['head'] = head_text
            head_['path'] = pathlib.Path(f).absolute()
            heads.append(head_)

    organizations = list(filter(lambda x: x.get('kind') == "Organization", heads))
    solutions = list(filter(lambda x: x.get('kind') == "Solution", heads))
    workspaces = list(filter(lambda x: x.get('kind') == "Workspace", heads))
    webapps = list(filter(lambda x: x.get('kind') == "WebApp", heads))
    datasets = list(filter(lambda x: x.get('kind') == "Dataset", heads))

    for o in organizations:
        p = pathlib.Path(o.get('path'))
        content = p.open().read()
        head = o.get('head')
        deploy_organization(head=head, file_content=content)

    for s in solutions:
        p = pathlib.Path(s.get('path'))
        content = p.open().read()
        head = o.get('head')
        deploy_solution(head=head, file_content=content, deploy_dir=deploy_dir)

    for swa in webapps:
        p = pathlib.Path(swa.get('path'))
        content = p.open().read()
        head = o.get('head')
        deploy_swa(head=head, file_content=content)

    for w in workspaces:
        p = pathlib.Path(w.get('path'))
        content = p.open().read()
        head = o.get('head')
        deploy_workspace(head=head, file_content=content, deploy_dir=deploy_dir)

    for d in datasets:
        p = pathlib.Path(d.get('path'))
        content = p.open().read()
        head = o.get('head')
        deploy_dataset(head=head, file_content=content)
