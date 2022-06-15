# Babylon

Babylon is a tool designed to simplify interaction between Cosmo Tech solutions and the Azure environment.

The organization of the repository can be found on [this page](doc/organization.md)

A basic how-to about contribution can be found [here](doc/contribute.md)

## Installation

```bash
pip install .
```

## Dev mode installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Autocompletion

After install you can run the following command to get autocompletion (in bash):

```bash
echo 'eval "$(_BABYLON_COMPLETE=bash_source babylon)"' > ~/.bashrc
source ~/.bashrc
```

For other type of command line you can check [this link](https://click.palletsprojects.com/en/8.1.x/shell-completion/)
for official click documentation

## Environment

A set of commands allow interaction with an Environment

```bash
babylon environment --help
#Usage: babylon environment [OPTIONS] COMMAND [ARGS]...
#
#  Command group handling local environment information
#
#Options:
#  --help  Show this message and exit.
#
#Commands:
#  complete  Complete the current environment for missing elements
#  display   Display information about the current environment
#  init      Initialize the current environment
#  validate  Validate the current environment
```

This environment is a deployment environment and default to the current folder, it can be overridden by using the 
`-e / --environment` option for the base command. This option takes a path to the environment to use.

More information about the environment are available [here](doc/environment.md)