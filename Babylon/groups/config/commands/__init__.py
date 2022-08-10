from .create_deploy import create_deploy
from .create_platform import create_platform
from .display import display
from .edit_deploy import edit_deploy
from .edit_platform import edit_platform
from .select_deployment import select_deployment
from .select_platform import select_platform

list_commands = [
    create_deploy,
    create_platform,
    edit_platform,
    edit_deploy,
    display,
    select_platform,
    select_deployment,
]
