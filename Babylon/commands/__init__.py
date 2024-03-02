from .abba import abba
from .webapp import webapp
from .powerbi import powerbi
from .api import api
from .azure import azure
from .config import config
from .vault import vault
from .git_hub import github
from .namespace import namespace
from .macro.apply import apply
from .macro.destroy import destroy

list_groups = [abba, api, azure, config, powerbi, webapp, vault, github, namespace, apply, destroy]
