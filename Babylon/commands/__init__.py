from .webapp import webapp
from .powerbi import powerbi
from .api import api
from .azure import azure
from .config import config
from .vault import vault
from .git_hub import github
from .terraform_cloud import terraform_cloud

list_groups = [
    api,
    azure,
    config,
    powerbi,
    webapp,
    vault,
    github,
    terraform_cloud,
]
