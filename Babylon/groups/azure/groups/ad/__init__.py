from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def ad():
    """Group interacting with Azure Active Directory"""


for _command in list_commands:
    ad.add_command(_command)

for _group in list_groups:
    ad.add_command(_group)
