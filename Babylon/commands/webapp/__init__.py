from click import group
from Babylon.utils.environment import Environment
from .deploy import deploy
from .export_config import export_config
from .upload_file import upload_file
from .upload_many import upload_many
from .download import download
from .update_workflow import update_workflow

env = Environment()

list_commands = [
    deploy,
    export_config,
    upload_file,
    download,
    update_workflow,
    upload_many,
]


@group()
def webapp():
    """Group handling Cosmo Sample WebApp configuration"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_ORG_NAME", "BABYLON_TOKEN"])


for _command in list_commands:
    webapp.add_command(_command)
