from click import group

from .delete import delete
from .get import get
from .get_all import get_all
from .download import download
from .upload import upload
from .download_all import download_all

list_commands = [delete, get, download, upload, get_all, download_all]


@group()
def report():
    """Command group handling PowerBI reports"""
    pass


for _command in list_commands:
    report.add_command(_command)
