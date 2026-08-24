# Babylon

<p align="center">
  <img src="docs/assets/img/Babylon-logo.png" alt="Babylon Logo">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENCE.md)
[![Cosmotech](https://img.shields.io/badge/Cosmotech-ffb039?style=for-the-badge&logoColor=black)](https://cosmotech.com/)
[![End-User-Documentation](https://img.shields.io/badge/End_User_Documentation-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://cosmo-tech.github.io/Babylon-End-User-Doc/)
[![Documentation](https://img.shields.io/badge/Documentation-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://cosmo-tech.github.io/Babylon/)

**Babylon** is the official command-line interface for provisioning, configuring, and managing
[Cosmo Tech](https://cosmotech.com/) solutions and platforms. It provides a unified babylon command that abstracts the Cosmo Tech API, Azure resources, and BI tooling such as Superset and Power BI.

With Babylon, you can scaffold, deploy, configure, and tear down environments through a consistent CLI workflow without maintaining custom scripts or managing each underlying service independently.

![Babylon CLI demo](/docs/assets/img/babylon-demo.gif)

## Installation

Babylon requires **Python 3.12+**. Installing it inside a virtual environment is strongly
recommended.

### Using `uv` (recommended)

If you don't have `uv` installed yet, follow the
[official instructions](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv venv
source .venv/bin/activate
uv pip install .
```

### Using `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

### Development install

Install Babylon in editable mode with the development dependency group (`ruff`, `pytest`):

```bash
uv pip install -e . --group dev
```

Verify the installation:

```bash
babylon --version
```

## Quick Start

```bash
# 1. Point Babylon at a context/tenant so it knows where to store state
babylon namespace use -c my-project -t my-tenant

# 2. Scaffold a new project (cloud provider + BI provider)
babylon init azure superset

# 3. Fill in project/variables.yaml with your environment values, then deploy
babylon apply project/

# 4. Inspect the deployed resources through the API
babylon api organizations get --oid <organization_id>
```

## Usage

Every Babylon invocation follows the same pattern:

```bash
babylon [GLOBAL OPTIONS] <COMMAND> [SUBCOMMAND] [ARGS] [OPTIONS]
```

### Global options

| Option | Description |
| --- | --- |
| `-v, --verbosity` | Set the logging verbosity (e.g. `DEBUG`, `INFO`, `WARNING`). |
| `-n, --dry-run` | Run commands in dry-run mode without applying changes. |
| `--log-path PATH` | Directory where `babylon.log` is written (defaults to the current directory). |
| `--kube-context TEXT` | Use a specific kubeconfig context instead of the current one. |
| `--version` | Print the installed Babylon version and exit. |
| `--help` | Show help for any command or subcommand. |

Discover any command's options at any time:

```bash
babylon --help
babylon apply --help
babylon api organizations --help
```

## CLI Commands

Babylon's commands are organized into two layers: high-level **macros** that orchestrate common
workflows, and a lower-level **API** command tree for granular control.

### Macros

| Command | Description |
| --- | --- |
| `babylon init <cloud_provider> <bi_provider>` | Scaffold a new project structure (YAML manifests, variables file, dashboard folders, Terraform web app module). |
| `babylon apply <deploy_dir>` | Deploy organizations, solutions, workspaces, and web apps described in `<deploy_dir>`. |
| `babylon destroy` | Tear down the resources tracked in the current state (requires confirmation, or `-y`). |
| `babylon namespace use` | Switch to (or create) a context/tenant namespace used to isolate project state. |
| `babylon namespace get-contexts` | Show the currently active context and tenant. |
| `babylon namespace get-all-states` | List local and remote state files available for the current namespace. |

### API

The `babylon api` group exposes the underlying Cosmo Tech API resources directly:

| Command | Description |
| --- | --- |
| `babylon api organizations` | Manage organizations (create, get, update, delete). |
| `babylon api solutions` | Manage solutions. |
| `babylon api workspaces` | Manage workspaces. |
| `babylon api datasets` | Manage datasets. |
| `babylon api runners` | Manage runners. |
| `babylon api runs` | Manage scenario runs. |
| `babylon api about` | Retrieve API version and metadata information. |

### Dashboards

| Command | Description |
| --- | --- |
| `babylon superset delete-assets` | Delete dashboard assets from a Superset instance. |

> Run `babylon <group> --help` to list every subcommand and its options — for example
> `babylon api organizations --help`.

## Examples

**Create and deploy a full project from scratch:**

```bash
babylon namespace use -c demo -t sandbox
babylon init azure superset
# edit project/variables.yaml with your resource values
babylon apply project/
```

**Deploy only the workspace, skipping the organization and solution:**

```bash
babylon apply --include workspace project/
```

**Deploy everything except the web app:**

```bash
babylon apply --exclude webapp project/
```

**Tear down a deployment without the confirmation prompt:**

```bash
babylon destroy --yes
```

**Get machine-readable output from an API command:**

```bash
babylon api workspaces get --oid <organization_id> --wid <workspace_id> -o json
```

**Run any command in dry-run mode to preview its effect:**

```bash
babylon --dry-run apply project/
```

## Configuration

Babylon stores per-project settings in a `variables.yaml` file (generated by `babylon init`) and
tracks deployment state under a local namespace defined by `babylon namespace use -c <context> -t <tenant>`.

- **`variables.yaml`**: resource-specific values (organization name, solution version, cloud
  provider settings, etc.) used to render the YAML manifests during `apply`.
- **State files**: one state file per context/tenant, listed with `babylon namespace get-all-states`
  and inspected with `babylon namespace get-contexts`.
- **Logs**: every run is logged to `babylon.log` in the directory given by `--log-path` (defaults
  to the current working directory).

## Development

Contributions are welcome! A detailed contribution guide is available in the
[project documentation](https://cosmo-tech.github.io/Babylon/latest/concepts/contribute/).

```bash
git clone git@github.com:Cosmo-Tech/Babylon.git
cd Babylon
uv venv
source .venv/bin/activate
uv pip install -e . --group dev
```

Run the test suite and linter before opening a pull request:

```bash
pytest
ruff check .
```

## Release Process

To publish a new release:

1. Ensure all planned features are merged into `main` (JIRA board).
2. Verify that:
   - CI tests are green ➜ [GitHub Actions](https://github.com/Cosmo-Tech/Babylon/actions)
   - The quality gate passes ➜ [SonarQube](https://sonarqube.cosmotech.com/dashboard?id=Babylon-main)
   - Dependencies are up to date (`uv lock --upgrade`)
   - There are no critical vulnerabilities ➜ [Dependency-Track](https://dep-track.cosmotech.com/projects/b79e84bb-f445-4b32-a56c-5c82c0064aff)
3. Bump the version in `Babylon/version.py` following [SemVer](https://semver.org/).
4. Regenerate the lock file: `uv lock`.
5. Tag the release: `git tag -a -m "5.4.0" 5.4.0`.
6. Push the tag: `git push origin tag 5.4.0`.
7. Write and publish release notes on [GitHub Releases](https://github.com/Cosmo-Tech/Babylon/releases).

## License

Babylon is released under the [MIT License](LICENCE.md).