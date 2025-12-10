from .api import api
from .macro.apply import apply
from .macro.destroy import destroy
from .macro.init import init
from .namespace import namespace

list_groups = [api, namespace, apply, destroy, init]
