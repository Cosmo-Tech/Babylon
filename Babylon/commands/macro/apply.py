import yaml
import click
import pathlib
import os

from logging import getLogger
from click import Path, argument, command, option
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
@option('-f',
        '--file',
        type=Path(file_okay=True, exists=True),
        default=["./variables.yaml"],
        multiple=True,
        help='Specify the of your variable file. By default, it takes the variables.yaml file.')
def apply(deploy_dir: pathlib.Path, file: [pathlib.Path]):
    """Macro Apply"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
    files = list(pathlib.Path(deploy_dir).iterdir())
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    env.set_var_files(file)
    resources = []
    for f in files_to_deploy:
        resource = dict()
        with open(f) as input_file:
            content = input_file.read()
            escaped_content = content.replace("{{", "${").replace("}}", "}")
            yaml_data = yaml.safe_load(escaped_content)
            resource['kind'] = yaml_data.get('kind')
            resource['namespace'] = yaml.safe_dump(yaml_data.get('namespace'))
            resource['content'] = escaped_content
            resources.append(resource)

    organizations = list(filter(lambda x: x.get('kind') == "Organization", resources))
    solutions = list(filter(lambda x: x.get('kind') == "Solution", resources))
    workspaces = list(filter(lambda x: x.get('kind') == "Workspace", resources))
    webapps = list(filter(lambda x: x.get('kind') == "WebApp", resources))
    datasets = list(filter(lambda x: x.get('kind') == "Dataset", resources))

    for o in organizations:
        content = o.get('content')
        namespace = o.get('namespace')
        deploy_organization(namespace=namespace, file_content=content)

    for s in solutions:
        content = s.get('content')
        namespace = s.get('namespace')
        deploy_solution(namespace=namespace, file_content=content, deploy_dir=deploy_dir)

    for swa in webapps:
        content = swa.get('content')
        namespace = swa.get('namespace')
        deploy_swa(namespace=namespace, file_content=content)

    for w in workspaces:
        content = w.get('content')
        namespace = w.get('namespace')
        deploy_workspace(namespace=namespace, file_content=content, deploy_dir=deploy_dir)

    final_datasets = []
    for d in datasets:
        content = d.get('content')
        namespace = d.get('namespace')
        deployed_dataset_id = deploy_dataset(namespace=namespace, file_content=content, deploy_dir=deploy_dir)
        if deployed_dataset_id:
            final_datasets.append(deployed_dataset_id)

    final_state = env.get_state_from_local()
    services = final_state.get('services')
    vars = env.get_variables()

    _ret = ['']
    _ret.append("")
    _ret.append("Deployments: ")
    _ret.append("")
    _ret.append(f"   * Organization   : {services.get('api').get('organization_id', '')}")
    _ret.append(f"   * Solution       : {services.get('api').get('solution_id', '')}")
    _ret.append(f"   * Workspace      : {services.get('api').get('workspace_id', '')}")
    for id in final_datasets:
        _ret.append(f"   * Dataset        : {id}")
    if services.get('webapp').get('static_domain', ''):
        _ret.append("   * WebApp         ")
        _ret.append(f"      * Hostname    : https://{services.get('webapp').get('static_domain', '')}")
    # Get the current working directory
    current_working_directory = os.getcwd()
    logfile_path = os.path.join(current_working_directory, "babylon.log")
    # Get the directory part of the log file path
    logfile_directory = os.path.dirname(logfile_path)
    _logs = ['']
    _logs.append("Babylon Logs: ")
    _logs.append("")
    if vars.get('path_logs'):
        _logs.append(f"   * The Babylon log and error files are generated at: {vars.get('path_logs')}")
    else:
        _logs.append(f"   * The Babylon log and error files are generated at: {logfile_directory}")
    click.echo(click.style("\n".join(_ret), fg="green"))
    click.echo(click.style("\n".join(_logs), fg="green"))
