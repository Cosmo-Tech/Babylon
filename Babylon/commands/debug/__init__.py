from click import group

from .get_workflow_pods import get_workflow_pods

list_commands = [
    get_workflow_pods,
]


@group()
def debug():
    """Add debug capacities of runs"""


for _command in list_commands:
    debug.add_command(_command)
