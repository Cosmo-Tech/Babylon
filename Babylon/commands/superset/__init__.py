from click import group

from .delete_assets import delete_assets


@group()
def superset():
    """Group handling communication with the Superset API."""
    pass


superset.add_command(delete_assets)
