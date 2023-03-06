from click import group

from .deploy import deploy
from .export_config import export_config
from .upload_file import upload_file
from .download import download
from .update_workflow import update_workflow

list_commands = [
    deploy,
    export_config,
    upload_file,
    download,
    update_workflow,
]


@group()
def webapp():
    """Group handling Cosmo Sample WebApp configuration"""
    pass


for _command in list_commands:
    webapp.add_command(_command)
