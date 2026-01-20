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

For development mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage
After installation, you can use the `babylon` command in your terminal.

```bash
babylon namespace use -c <context_id> -t <tenant_id> -s <state_id>

babylon init

babylon apply --organization project/

babylon apply --solution project/

babylon apply --workspace project/

babylon apply --dataset project/

babylon apply --runner project/
```

## Release

To release a new version follow the checklist:
- Make sure all features are merged on main (JIRA board)
- Verify that:
  - CI tests are green [Github Actions](https://github.com/Cosmo-Tech/Babylon/actions)
  - Sonarqube quality gate passes [sonarqube](https://sonarqube.cosmotech.com/dashboard?id=Babylon-main)
  - Dependency track has no critical vulnerabilities [DependencyTrack](https://dep-track.cosmotech.com/projects/b79e84bb-f445-4b32-a56c-5c82c0064aff)
- Increment the version number (`VERSION`) `/Babylon/version.py` following [semver](https://semver.org/) rules
- Generate lock file `uv lock`
- Make a git tag, `git tag -a -m "5.0.0-beta.2" 5.0.0-beta.2`
- Push the tag `git push tag 5.0.0-beta.2`
- Write release notes publish on [GitHub](https://github.com/Cosmo-Tech/Babylon/releases)