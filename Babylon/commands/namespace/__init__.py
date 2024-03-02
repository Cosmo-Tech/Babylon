from click import group
from Babylon.commands.namespace.use import use
from Babylon.utils.environment import Environment

env = Environment()


@group()
def namespace():
    """Babylon namespace"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


list_groups = [use]

for _group in list_groups:
    namespace.add_command(_group)
