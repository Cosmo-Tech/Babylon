from .delete import delete
from .get import get
from .take_over import take_over
from .get_all import get_all
from .update_credentials import update_credentials

list_commands = [
    update_credentials,
    delete,
    get,
    take_over,
    get_all,
]
