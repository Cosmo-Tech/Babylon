# How-to contribute to Babylon

## Creating a new group of commands

### Create a new package inside `Babylon.groups`

This new package comes with a package called `commands` and you can use the following template for
the `new_group.__init__.py`

```python
from click import group
from click import pass_context
from .commands import list_commands


@group()
@pass_context
def new_group(ctx):
    """New group of commands"""
    ctx.obj = dict()  # this obj can be passed to the commands of the group by using the click.pass_obj decorator


for _command in list_commands:
    new_group.add_command(_command)
```

### Initialize the `commands.__init__.py`

You can use the following template to initialize the `new_group.commands.__init__.py`

```python
list_commands = []
```

### Add your group to the groups callable by the cli

You have to add an import for your group in the `Babylon.groups.__init__.py`

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

## Adding a new command to an existing group

### Template

This template can be copied in the `commands` package for the group we want to add the command to.

```python
from click import command
from click import pass_obj

from Babylon.utils.decorators import timing_decorator

import logging

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def my_command(ctx):
    """Doc-string for my new command"""
    pass
```

### Add to `commands.__init__.py`

Once the command is created you can make a link to it in the `commands.__init__.py` file

```python
from .older_command import older_command
from .my_command import my_command  # You import your new command here

list_commands = [
    older_command,
    my_command,  # And you add it to the list of existing commands here
]
```

And that's all folks, you added your command to an existing group of commands