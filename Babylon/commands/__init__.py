from .api import api
from .azure import azure
from .macro.apply import apply
from .macro.destroy import destroy
from .macro.init import init
from .namespace import namespace
from .powerbi import powerbi
from .vault import vault

list_groups = [api, azure, powerbi, vault, namespace, apply, destroy, init]
