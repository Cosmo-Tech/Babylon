from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .last_run import last_run
from .outputs import outputs
from .run import run

list_commands = [
    create,
    delete,
    get,
    get_all,
    last_run,
    outputs,
    run,
]
