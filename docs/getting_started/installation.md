# Installation


```bash
git clone git@github.com:Cosmo-Tech/Babylon.git
cd Babylon
pip install .
```

## Dev mode installation

If you want to develop on top of Babylon you can set it up in developer mode (`-e`).

And if you don't want to multiply versions of Babylon, you can also add it in a virtual environment (requires `venv` or `pyenv`) 

1. venv:

    ```bash
    python -m venv .venv       # Create your venv named .venv
    source .venv/bin/activate  # Activate your venv
    pip install -e .           # Install Babylon in developer mode
    ```


For other type of command line you can check [this link](https://click.palletsprojects.com/en/8.1.x/shell-completion/){:target="_blank"}
for official click documentation