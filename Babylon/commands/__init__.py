from .abba import abba
from .webapp import webapp
from .powerbi import powerbi
from .api import api
from .azure import azure
from .config import config
from .vault import vault
from .git_hub import github
from .plugin import plugin
from .state import state
from .namespace import namespace
from .deploy import capply

list_groups = [capply, abba, api, azure, config, plugin, powerbi, webapp, vault, github, state, namespace]
