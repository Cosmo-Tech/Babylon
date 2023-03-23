from click import group

from .get_all import get_all
from .run import run
from .run_folder import run_folder

list_commands = [
    get_all,
    run,
    run_folder
]



@group()
def script():
    """Group interacting with Azure Data Explorer scripts"""
    pass

for _command in list_commands:
    script.add_command(_command)
