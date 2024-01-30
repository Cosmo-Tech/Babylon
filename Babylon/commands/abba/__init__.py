from click import group

from Babylon.commands.abba.scenarioruns import scenarioruns


@group()
def abba():
    """Cosmotech ABBA"""
    pass


list_groups = [scenarioruns]

for _group in list_groups:
    abba.add_command(_group)
