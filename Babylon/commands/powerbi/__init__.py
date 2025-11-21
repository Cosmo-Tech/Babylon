from click import group

from Babylon.utils.environment import Environment

from .dataset import dataset
from .report import report
from .resume import resume
from .suspend import suspend
from .workspace import workspace

env = Environment()

list_groups = [
    dataset,
    workspace,
    report,
]

list_commands = [workspace, resume, suspend]


@group()
def powerbi():
    """Group handling communication with PowerBI API\n
    \b
    Optional:\n
    Environment variable to get access token with a user email\n
    - BABYLON_ENCODING_KEY
    """
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    powerbi.add_command(_command)

for _group in list_groups:
    powerbi.add_command(_group)
