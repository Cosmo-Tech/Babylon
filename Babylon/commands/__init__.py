from .webapp import webapp
from .powerbi import powerbi
from .api import api
from .azure import azure
from .config import config
from .terraform_cloud import terraform_cloud
from .working_dir import working_dir

list_groups = [
    webapp,
    powerbi,
    terraform_cloud,
    azure,
    config,
    api,
    working_dir,
]
