from click import group

from .set import set  
  
list_commands = [ set ]


@group()
def permission():
    """Group interacting with Azure Permissions"""
    pass


for _command in list_commands:
    permission.add_command(_command)
