from click import group

from .deploy_workspace import deploy_workspace
from .resume import resume
from .suspend import suspend
from .dataset import dataset
from .workspace import workspace
from .report import report

list_groups = [
    dataset,
    workspace,
    report,
]

list_commands = [
    deploy_workspace,
    resume,
    suspend
]


@group()
def powerbi():
    """Group handling communication with PowerBI API"""


for _command in list_commands:
    powerbi.add_command(_command)

for _group in list_groups:
    powerbi.add_command(_group)
