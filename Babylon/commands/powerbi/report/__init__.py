from click import group

from .delete import delete
from .download import download
from .download_all import download_all
from .get import get
from .get_all import get_all
from .pages import pages
from .upload import upload

list_commands = [delete, get, download, upload, get_all, download_all, pages]


@group()
def report():
    """Command group handling PowerBI reports"""
    pass


for _command in list_commands:
    report.add_command(_command)
