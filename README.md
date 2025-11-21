# Babylon

[![End-User-Documentation](https://img.shields.io/badge/End_User_Documentation-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://cosmo-tech.github.io/Babylon-End-User-Doc/)
[![Documentation](https://img.shields.io/badge/Documentation-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://cosmo-tech.github.io/Babylon/)
[![Cosmotech](https://img.shields.io/badge/Cosmotech-ffb039?style=for-the-badge&logoColor=black)](https://cosmotech.com/)

Babylon is a tool designed to simplify configuration and management of the Cosmo Tech solutions and platform.

A basic how-to about contribution can be found there : [![Contribution](https://img.shields.io/badge/Contribution-%23121011.svg?style=for-the-badge&logoColor=black)](https://cosmo-tech.github.io/Babylon/latest/concepts/contribute/)

## Installation

Install babylon in a virtual environment:

### Install with uv (recommended)

If you don't have `uv` installed do so following [instructions](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv venv
source .venv/bin/activate
uv pip install .
```

For development mode:

```bash
uv pip install -e . --group dev
```

### Install using pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

## Usage
After installation, you can use the `babylon` command in your terminal.