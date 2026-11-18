# Deployment state

State records the resource identifiers that Babylon uses to update or destroy
a deployment. It is separate from authentication configuration and from
`variables.yaml`. Preserve it as part of the project's operational data.

## Locations and namespace

The context/tenant pair selects a state file:

- Active namespace: `~/.config/cosmotech/babylon/namespace.yaml`.
- Local state: `~/.config/cosmotech/babylon/state.<context>.<tenant>.yaml`.
- Remote state, when enabled: the Kubernetes Secret
  `babylon-state-<context>-<tenant>` in the tenant namespace, with a `state.yaml`
  data key.

The current remote backend is **Kubernetes Secrets**, not the Azure Blob
container described in earlier documentation. `namespace.remote: true` in a
manifest enables remote persistence; the generated manifests obtain it from
the `remote` variable.

Local-only state does not make deployment offline: API access and configured
sidecars still require their respective services. Use a unique context for each
independently managed deployment.

## Inspect state

```bash
babylon namespace get-contexts
babylon namespace get-states local
babylon namespace show-state local
babylon namespace get-states remote
babylon namespace show-state remote
```

Remote operations require access to the selected cluster and tenant namespace.
`show-state` supports structured output, for example:

```bash
babylon namespace show-state local -o json
babylon namespace show-state remote -f deployment-state.yaml
```

Treat state exports as operationally sensitive. Do not commit credentials or
unreviewed environment-specific state files.

## Structure and synchronization

A simplified Superset deployment state looks like this:

```yaml
context: my-project
tenant: my-tenant
remote: true
services:
  api:
    organization_id: o-example
    solution_id: sol-example
    workspace_id: w-example
  dashboards:
    superset:
      qadashboardsatisfaction:
        uuid: <embedded-dashboard-uuid>
        original_id: "1"
  postgres:
    schema_name: w_example
    provider: superset
  webapp:
    webapp_name: business
    webapp_url: https://<webapp-host>
```

The schema can evolve between releases. Do not edit resource IDs merely to
select a different project. Switch the namespace instead.

Successful macro operations save state locally and synchronize the remote
Secret when remote persistence is enabled. Keep the local state and correct
cluster access available; if a remote Secret is missing, Babylon can bootstrap
it from existing local API resource IDs.

## Dashboard identifiers

On deployment, Babylon records identifiers returned by the dashboard provider:

- Superset stores embedded UUIDs and original dashboard IDs under
  `services.dashboards.superset`.
- Power BI stores `workspace_id` and the report mapping under
  `services.dashboards.powerbi`.

Subsequent deployments use these values to render dashboard references in the
workspace payload. Leave the template expressions in project manifests so the
same configuration can be reused across independently managed deployments.
See the [Superset](../examples/superset.md) and
[Power BI](../examples/powerbi.md) examples for naming conventions.

## Cleanup

After a partial `destroy`, remaining state is saved locally and remotely when
enabled. Once all tracked resource IDs are cleared, the macro removes the local
state file and the remote Secret. Review cleanup errors before discarding
backups. Never delete state as a substitute for
[destroying its resources](../tutorial/destroy.md).
