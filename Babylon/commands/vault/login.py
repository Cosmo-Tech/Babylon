import inquirer

from click import command
from hvac import Client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()


@command()
def login() -> CommandResponse:
    """
    Login vault hashicorp
    """
    env.check_environ([
        "BABYLON_SERVICE",
    ])
    questions = [
        inquirer.Text('username', message="Username", validate=lambda _, x: str.isalnum(x)),
        inquirer.Password('password', message="Password"),
        inquirer.Text('organization', message="Organization")
    ]

    answers = inquirer.prompt(questions)
    username = answers['username']
    password = answers['password']
    organization = answers['organization']
    client = Client(url=env.server_id)
    token = client.auth.userpass.login(username=username, password=password, mount_point=f"userpass-{organization}")
    print(f"export BABYLON_TOKEN={token['auth']['client_token']}")
    print(f"export BABYLON_ORG_NAME={organization}")
    return CommandResponse.success()
