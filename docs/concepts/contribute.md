# How-to contribute to Babylon

Babylon use a hierarchy of groups, subgroups, and commands to allow the user to guide him. So if you want to create a
new set of commands you will want to make sure to group them in a logical structure.

## Guidelines

Babylon code style is enforced with three tools that block pull requests and push on the main branch.

### Formatting with yapf
A `.style.yapf` file is included at the root of the project and specifies specific parameters Babylon uses. Please integrate `yapf` autoformatting within your IDE choice.

### Linting with Flake8
A `.flake8` file is included at the root of the project and specifies specific parameters Babylon uses. Please integrate `flake8` linting within your IDE of choice.

### Testing with pytest
Units tests are located in the `tests` folder. Tests should be run when the `Babylon/utils` are modified as it is for now the only part of the code that is automated.

## The plugin `babylon dev-tools`

The plugin `babylon dev-tools` is available, once you added it you can do `babylon dev-tools --help` to check the existing commands

### Adding the plugin

In the folder you cloned Babylon you can do the following command to activate the plugin

```bash
babylon config plugin add plugins/dev_tools
```

After running this command you will have access to the plugin in you babylon

## Create a command

In this part you will learn to do what the commands of initialization have automatized.

### Creating a new group of commands

#### Create a folder inside `Babylon.commands`

A module will contain an `__init__.py` file containing a `click` Group function. A template can be found in the following location. 

```python
from click import group
from click import Group
from click import Command

list_commands: list[Command] = []
list_groups: list[Group] = []


@group()
def group_template():
    """Group initialized from a template"""
    pass


for _command in list_commands:
    group_template.add_command(_command)

for _group in list_groups:
    group_template.add_command(_group)
```

#### Add your group to the groups callable by the cli

You have to add an import for your group in the `Babylon.commands.__init__.py`

```python
from .api import api
from .new_group import new_group  # Add your import here

command_groups = [
    api,
    new_group,  # Add your group command to the list of existing commands
]
```

And your new group is then ready to be called

```bash
babylon new-group
#Usage: babylon new-group [OPTIONS] COMMAND [ARGS]...
#
#  New group of commands
#
#Options:
#  --help  Show this message and exit.
#
#Commands:
#  my_command  Doc-string for my new command
```

### Adding a sub-group in an existing group

You follow the same instruction as adding a group in `Babylon.groups` but in a sub-module.

### Adding a new command to an existing group

#### Template

This template can be copied in the group module we want to add the command to.

```python
import logging

from click import command

logger = logging.getLogger("Babylon")


@command()
def command_template():
    """Command created from a template"""
    logger.warning("This command was initialized from a template and is empty")
```

#### Add to `__init__.py`

Once the command is created you can make a link to it in the group `__init__.py` file

```python
from .older_command import older_command
from .my_command import my_command  # You import your new command here

list_commands = [
    older_command,
    my_command,  # And you add it to the list of existing commands here
]
```

And that's all folks, you added your command to an existing group of commands