from click import group

from Babylon.commands.namespace.get_all_states import get_states
from Babylon.commands.namespace.get_contexts import get_contexts
from Babylon.commands.namespace.use import use
from Babylon.utils.environment import Environment

env = Environment()


@group()
def namespace():
    """Babylon namespace"""
    pass


list_groups = [use, get_contexts, get_states]

for _group in list_groups:
    namespace.add_command(_group)
