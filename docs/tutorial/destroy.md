# Destroy a deployment

!!! danger "Destructive operation"
    `babylon destroy` deletes resources tracked in the active state. Deleting a
    workspace also removes its associated sidecars and data. Check resource
    ownership and backups first; this is not a reversible operation.

## Verify the target

From the deployment working directory, inspect both the Kubernetes context and
the Babylon namespace:

```bash
kubectl config current-context
babylon namespace get-contexts
babylon namespace show-state local
```

For deployments with remote state, also inspect:

```bash
babylon namespace show-state remote
```

If necessary, select the intended namespace again:

```bash
babylon namespace use -c my-project -t my-tenant
```

## Remove the deployment

Keep the project configuration and Terraform checkout available until cleanup
has finished, then run:

```bash
babylon destroy
```

Read the listed resource IDs and confirm only when they match the deployment
you intend to remove. The macro handles tracked organizations, solutions,
workspaces, provider dashboard assets, PostgreSQL schemas, workspace Secrets
and ConfigMaps, and the Terraform web app.

For an explicitly reviewed automated cleanup, `babylon destroy --yes` bypasses
the confirmation prompt.

## Select a subset

```bash
# Remove the workspace and its sidecars, retaining shared parent resources.
babylon destroy --include workspace

# Preserve the organization while removing other tracked resources.
babylon destroy --exclude organization
```

Repeat the same selection option to select several kinds; do not combine
`--include` and `--exclude`. Dependencies still matter: retaining a child while
deleting its parent may fail or remove more than intended at the platform level.

If deployment used custom variables, supply the same files:

```bash
babylon destroy --var-file deployment.yaml --include webapp
```

After partial cleanup Babylon saves the remaining state locally and, if enabled,
remotely. After all tracked resource IDs are cleared, it removes the local state
file and remote state Secret. Review the command output for failed cleanup or
remaining provider resources before deleting your project files. See
[deployment state](../guides/state.md) for storage details.
