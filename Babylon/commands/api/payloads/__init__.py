from click import group
from .upsert import upsert

list_commands = [upsert]


@group()
def payloads():
    """Create or update a payload from API resource"""


for _group in list_commands:
    payloads.add_command(_group)
