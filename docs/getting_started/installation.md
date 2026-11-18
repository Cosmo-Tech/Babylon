# Installation

Babylon requires **Python 3.12 or later** and Git. Install it in a virtual
environment to keep dependencies isolated from other Python applications.

## Get the sources

```bash
git clone https://github.com/Cosmo-Tech/Babylon.git
cd Babylon
```

To use a particular release, check out its tag before installing. Available tags
are listed on the [releases page](https://github.com/Cosmo-Tech/Babylon/releases).

## Install with uv (recommended)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

=== "Linux / macOS"

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install .
    ```

=== "Windows PowerShell"

    ```powershell
    uv venv
    .\.venv\Scripts\Activate.ps1
    uv pip install .
    ```

## Install with pip

=== "Linux / macOS"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install .
    ```

=== "Windows PowerShell"

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install .
    ```

For an editable development installation, use
`uv pip install -e . --group dev` instead.

## Verify the installation

```bash
babylon --version
babylon --help
```

Installing the CLI does not grant platform access. Continue with
[configuration](configuration.md) before making API calls.

## Deployment tools

Install [kubectl](https://kubernetes.io/docs/tasks/tools/) and obtain an authorized
kubeconfig for the target tenant. Workspace sidecars and remote state require
Kubernetes access even when API authentication comes from environment variables.

Web app deployment also requires
[Terraform](https://developer.hashicorp.com/terraform/install) and access to the
[terraform-webapp module](https://github.com/Cosmo-Tech/terraform-webapp).
Use the Terraform version required by the selected module release.
Azure-backed deployments additionally require the
[Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) and
appropriate [Azure permissions](../guides/azure.md).
