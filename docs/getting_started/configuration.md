# Configure Babylon

Babylon separates API authentication, the active context/tenant, and deployment
state. Ask your platform administrator for the correct tenant and credentials;
installing Babylon does not provision a Cosmo Tech platform.

## Select the Kubernetes context

```bash
kubectl config current-context
kubectl config get-contexts
kubectl config use-context <target-context>
```

The global `--kube-context` option can select a context for an invocation without
changing the current kubeconfig context:

```bash
babylon --kube-context <target-context> api about
```

!!! warning "Check both contexts"
    A Kubernetes context selects the cluster and identity. A Babylon context
    isolates a project's state. They are different settings: verify both before
    making changes.

## Select the Babylon namespace

Choose a unique context for the deployment and use the Kubernetes namespace as
the tenant:

```bash
babylon namespace use -c my-project -t my-tenant
babylon namespace get-contexts
```

The active selection is stored in
`~/.config/cosmotech/babylon/namespace.yaml`. Use a separate context for every
independently managed workspace so that their state files do not collide.

## Configure API authentication

### Kubernetes Secret (default)

Babylon reads the `babylon-config` Secret in the selected tenant namespace.
Its decoded configuration must contain `api_url`, `keycloak_client_id`,
`keycloak_client_secret`, and `keycloak_token_url`. Ask the administrator to
provision the Keycloak client and grant the necessary API permissions.

Your Kubernetes identity needs permission to read that Secret; remote state and
workspace deployments require additional resource permissions. Do not copy
decoded Secrets into tickets, logs, or version control.

### Environment variables

For API-only use or CI, provide **all four** variables below through your
approved secret-management mechanism:

```bash
export API_URL="https://<platform-host>/<tenant>/v5"
export KEYCLOAK_CLIENT_ID="cosmotech-babylon-client"
export KEYCLOAK_CLIENT_SECRET="<client-secret>"
export KEYCLOAK_TOKEN_URL="https://<keycloak-host>/realms/<realm>/protocol/openid-connect/token"
```

In PowerShell, use `$env:NAME = "value"` instead of `export NAME="value"`.
The URLs and client ID are examples: use the values for your deployment.
If any of these environment variables is absent, Babylon falls back to the
Kubernetes Secret rather than merging partial API credentials.

!!! note "API configuration is not all deployment configuration"
    These variables replace API authentication only. PostgreSQL, Superset,
    remote state, and web app deployment can still require Kubernetes Secrets,
    cluster access, and provider credentials.

## Verify access

```bash
babylon api about
babylon api organizations list -o wide
```

If authentication fails, check the selected cluster and tenant, Secret access,
the Keycloak token endpoint, and the client's permissions. An environment
variable override can also point to a different platform than your kubeconfig.

API commands that support structured output can display JSON or YAML or save it
to a file:

```bash
babylon api organizations list -o json
babylon api organizations list -f organizations.yaml
```

See each command's help or the [CLI reference](../references/cli.md) for available
output options. Next, [deploy a workspace](../tutorial/deploy.md) and learn how
[state is persisted](../guides/state.md).
