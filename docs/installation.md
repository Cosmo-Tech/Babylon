# Installation

```bash
git clone git@github.com:Cosmo-Tech/Babylon.git
cd Babylon
pip install .
```

## Running Babylon with Docker
```bash
docker pull ghcr.io/cosmo-tech/babylon:latest
mkdir config workingdir
docker run -it --rm --mount type=bind,source="$(pwd)"/config,target=/opt/babylon/config --mount type=bind,source="$(pwd)"/workingdir,target=/etc/babylon/workingdir babylon
```
Then you can access and edit the following host directories:
- Configuration is in host `config/` directory, (`/opt/babylon/config/` in the container)
- Configuration is in host `workingdir/` directory, (`/etc/babylon/workingdir/` in the container)

## Dev mode installation

If you want to develop on top of Babylon you can set it up in developer mode (`-e`)

And if you don't want to multiply versions of Babylon, you can also add it in a virtual environment (requires `venv`) 

```bash
python -m venv .venv       # Create your venv named .venv
source .venv/bin/activate  # Activate your venv
pip install -e .           # Install Babylon in developer mode
```

The next line is optional, run it if you want to have the dev-tools plugin to facilitate command & groups manipulation

```bash
babylon config plugin add plugins/dev_tools # Add the plugin dev_tools situated in the folder plugins/dev_tools
```

## Autocompletion

After install you can run the following commands to get autocompletion (in bash, and stays effective after restarts as you modify your `.bashrc`)

```bash
echo 'eval "$(_BABYLON_COMPLETE=bash_source babylon)"' >> ~/.bashrc
source ~/.bashrc
```

You can also only run the following command to have autocompletion until you close your current terminal :

```bash
eval "$(_BABYLON_COMPLETE=bash_source babylon)"
```

For other type of command line you can check [this link](https://click.palletsprojects.com/en/8.1.x/shell-completion/)
for official click documentation