# How-to contribute to Babylon

Babylon use a hierarchy of groups, subgroups, and commands to allow the user to guide him. So if you want to create a
new set of commands you will want to make sure to group them in a logical structure.

## Use `babylon self` to initialize

You can use `babylon self initialize-group` to initialize all the files for a new group (works with subgroups too)

```bash
babylon self initialize-group mynewgroup mynewsubgroup
# This command will try to create the group mynewsubgroup in mynewgroup
# if mynewgroup does not exist it will create it first
```

After running the previous command you will have this new structure added to the project

```text
Babylon
├── groups/
│   ├── __init__.py            < This file is modified to add the new command to the cli
│   ├── ...
│   └── mynewgroup/            < This folder is created
│       ├── __init__.py        < This file is initialized
│       ├── commands/          < This folder is created
│       |   └── __init__.py    < This file is initialized
│       └── groups/            < This folder is created
│           ├── __init__.py    < This file is initialized and then modified to add the new subcommand to the cli
│           └── mynewsubgroup/ < This folder is created (with the same hierarchy as mynewgroup inside)
└── ...
```

You can use `babylon self initialize-command` to initialize a new command (will initialize the required groups if non
existent). You can add as many groups as you want (starting from 0 groups)

```bash
babylon self initialize-command mynewgroup mynewcommand
# This command will try to create the command mynewcommand in mynewgroup
# if mynewgroup does not exist it will create it first
```

After running the previous command you will have the following change to the structure

```text
Babylon
├── groups/
│   ├── ...
│   └── mynewgroup/
│       ├── commands/
│       |   ├── mynewcommand.py < This file is initialized
│       |   └── __init__.py     < This file is modified to add the new command to the cli
│       └── ...
└── ...
```

If you want to do it by hand you can check the following sections for a manual approach to creating a group / subgroup /
command

## Create files by hand

In this part you will learn to do what the commands of initialization have automatized.

### Creating a new group of commands

#### Create a new package inside `Babylon.groups`

This new package comes with a package called `commands` and a package named `groups` and you can use the following
template for the `new_group.__init__.py`

```python
from click import group
from click import pass_context
from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def new_group(ctx):
    """New group of commands"""
    ctx.obj = dict()  # this obj can be passed to the commands of the group by using the click.pass_obj decorator


for _command in list_commands:
    new_group.add_command(_command)

for _group in list_groups:
    new_group.add_command(_group)
```

#### Initialize the `commands.__init__.py`

You can use the following template to initialize the `new_group.commands.__init__.py`

```python
list_commands = []
```

#### Initialize the `groups.__init__.py`

You can use the following template to initialize the `new_group.commands.__init__.py`

```python
list_groups = []
```

#### Add your group to the groups callable by the cli

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

### Adding a sub-group in an existing group

You follow the same instruction as adding a group in `Babylon.groups` but in a sub-package.

- Create a new package in `Babylon.groups.<command>.groups`
- Add the new packages `Babylon.groups.<command>.groups.<subcommand>.commands`
  and `Babylon.groups.<command>.groups.<subcommand>.groups`
- Initialize the multiple `__init__.py` the same way as if you were creating a group for `Babylon`
- Add your group in the list of groups in the file `Babylon.groups.<command>.groups.__init__.py` instead of the one
  in `Babylon.groups.__init__.py`

### Adding a new command to an existing group

#### Template

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

#### Add to `commands.__init__.py`

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