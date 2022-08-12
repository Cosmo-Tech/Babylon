from .azure import azure
from .config import config
from .api import api
from .solution import solution
from .debug import debug
from .self import self

list_groups = [
    azure,
    config,
    api,
    solution,
    debug,
    self
]
