from .terraform_cloud import terraform_cloud
from .debug import debug
from .azure import azure
from .config import config
from .api import api
from .working_dir import working_dir

list_groups = [
    terraform_cloud,
    debug,
    azure,
    config,
    api,
    working_dir,
]
