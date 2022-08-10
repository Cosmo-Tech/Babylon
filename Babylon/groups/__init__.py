from .config import config
from .api import api
from .environment import environment
from .debug import debug
from .self import self

list_groups = [
    config,
    api,
    environment,
    debug,
    self
]
