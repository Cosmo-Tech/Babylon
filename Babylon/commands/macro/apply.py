import os
import yaml
import click
import pathlib

from logging import getLogger
from datetime import datetime
from click import Path, argument, command
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import injectcontext
from Babylon.commands.macro.deploy_webapp import deploy_swa
from Babylon.commands.macro.deploy_dataset import deploy_dataset
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_workspace import deploy_workspace
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
    start_time = datetime.now()
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    heads = []
    for f in files_to_deploy:
        head_ = dict()
        with open(f) as input_file:
            heads_list = [next(input_file) for _ in range(7)]
            head_text = "".join(heads_list)
            result = head_text.replace("{{", "${").replace("}}", "}")
            head = yaml.safe_load(result)
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
        head = s.get('head')
        deploy_solution(head=head, file_content=content, deploy_dir=deploy_dir)

    for swa in webapps:
        p = pathlib.Path(swa.get('path'))
        content = p.open().read()
        head = swa.get('head')
        deploy_swa(head=head, file_content=content)

    for w in workspaces:
        p = pathlib.Path(w.get('path'))
        content = p.open().read()
        head = w.get('head')
        deploy_workspace(head=head, file_content=content, deploy_dir=deploy_dir)

    final_datasets = dict()
    for d in datasets:
        p = pathlib.Path(d.get('path'))
        content = p.open().read()
        head = d.get('head')
        deployed_dataset = deploy_dataset(head=head, file_content=content, deploy_dir=deploy_dir)
        if deployed_dataset:
            final_datasets.update(deployed_dataset)

    final_state = env.get_state_from_local()
    services = final_state.get('services')

    error_file_path = pathlib.Path.cwd() / pathlib.Path(deploy_dir).parent / "error.log"
    if os.path.exists(error_file_path):
        error_file = open(error_file_path, 'r')
        _errors = ['']
        _errors.append("The following warnings or errors were returned and need to be looked at")
        lines = error_file.readlines()
        for line in lines:
            line_split = line.split(" ", 3)
            exact_time = line_split[1]
            date_time_format = exact_time.split(",")
            formatted_time = datetime.strptime(date_time_format[0], "%H:%M:%S")
            if formatted_time > start_time:
                _errors.append(line_split[3])
        if len(_errors) > 2:
            click.echo(click.style("\n".join(_errors), fg="red"))

    _ret = ['']
    _ret.append("")
    _ret.append("Deployments: ")
    _ret.append("")
    _ret.append(f"   * Organization   : {services.get('api').get('organization_id', '')}")
    _ret.append(f"   * Solution       : {services.get('api').get('solution_id', '')}")
    _ret.append(f"   * Workspace      : {services.get('api').get('workspace_id', '')}")
    for id, name in final_datasets:
        _ret.append(f"   * Dataset        : {id} - {name}")
    if services.get('webapp').get('static_domain', ''):
        _ret.append("   * WebApp         ")
        _ret.append(f"      * Hostname    : https://{services.get('webapp').get('static_domain', '')}")
    click.echo(click.style("\n".join(_ret), fg="green"))
