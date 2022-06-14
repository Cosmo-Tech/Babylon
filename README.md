# Babylon

Babylon is a tool designed to simplify interaction between Cosmo Tech solutions and the Azure environment.

The organization of the repository can be found on [this page](ORGANIZATION.md)

A basic how-to about contribution can be found [here](CONTRIBUTE.md)

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
