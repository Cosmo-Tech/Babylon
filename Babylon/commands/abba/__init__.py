from click import group


@group()
def abba():
    """Cosmotech ABBA"""
    pass


list_groups = []

for _group in list_groups:
    abba.add_command(_group)
