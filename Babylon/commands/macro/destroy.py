from click import command
from Babylon.utils.environment import Environment

env = Environment()


@command()
def destroy():
    """Macro Destroy"""
