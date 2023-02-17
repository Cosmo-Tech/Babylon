from .update_remote import update_remote
from .deploy import deploy
from .export_config import export_config
from .upload_file import upload_file
from .download import download
from .update_workflow import update_workflow

list_commands = [
    update_remote,
    deploy,
    export_config,
    upload_file,
    download,
    update_workflow,
]
