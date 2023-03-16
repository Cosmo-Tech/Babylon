from click import group

from .encrypt_file import encrypt_file
from .decrypt_file import decrypt_file
from .complete import complete
from .display import display
from .init import init
from .validate import validate
from .zip_env import zip_env
from .generate_secret_key import generate_secret_key

list_commands = [decrypt_file, encrypt_file, init, complete, validate, display, zip_env, generate_secret_key]


@group()
def working_dir():
    """Command group handling working directory information"""


for _command in list_commands:
    working_dir.add_command(_command)
