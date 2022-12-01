from .powerbi import powerbi
from .api import api
from .azure import azure
from .config import config
from .debug import debug
from .terraform_cloud import terraform_cloud
from .working_dir import working_dir

list_groups = [
    powerbi,
    terraform_cloud,
    debug,
    azure,
    config,
    api,
    working_dir,
]
