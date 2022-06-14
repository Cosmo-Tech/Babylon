from .adx import adx
from .azure import azure
from click import group


@group()
def v0():
    """Legacy commands for first version of babylon"""
    pass


for c in [adx, azure]:
    v0.add_command(c)
