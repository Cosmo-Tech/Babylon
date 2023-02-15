from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def appinsight():
    """Group interacting with Azure App Insight"""


for _command in list_commands:
    appinsight.add_command(_command)

for _group in list_groups:
    appinsight.add_command(_group)
