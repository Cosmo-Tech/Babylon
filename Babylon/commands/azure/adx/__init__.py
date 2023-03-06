from click import group

from .list_scripts import list_scripts
from .run_folder import run_folder
from .run_script import run_script
from .permission import permission

list_commands = [
    list_scripts,
    run_folder,
    run_script,
]

list_groups = [
    permission,
]


@group()
def adx():
    """Group interacting with Azure Data Explorer"""
    pass


for _command in list_commands:
    adx.add_command(_command)

for _group in list_groups:
    adx.add_command(_group)
