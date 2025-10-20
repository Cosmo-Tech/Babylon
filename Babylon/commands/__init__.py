from .webapp import webapp
from .powerbi import powerbi
from .api import api
from .azure import azure
from .vault import vault
from .git_hub import github
from .namespace import namespace
from .macro.apply import apply
from .macro.destroy import destroy
from .macro.init import init

list_groups = [api, azure, powerbi, webapp, vault, github, namespace, apply, destroy, init]
