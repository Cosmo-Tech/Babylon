# PostgreSQL workspace sidecars

The generated workspace manifests use PostgreSQL for runner results. Schema
initialization and optional SQL scripts run through Kubernetes jobs; they are
not the older ADX provisioning workflow.

## Schema and scripts

Configure the following under `spec.sidecars` in the workspace manifest:

```yaml
postgres:
  schema:
    create: true
    jobs:
      - name: k8s_job.yaml
        path: postgres/jobs
    scripts:
      - run: true
        path: postgres/scripts
```

Paths are relative to the deployment directory supplied to `apply`. Babylon
creates a dedicated workspace schema; its name replaces hyphens in the workspace
ID with underscores, for example `w-example` becomes `w_example`.

`init` creates sample scripts, but execution is disabled (`run: false`) by
default. Review or replace them before enabling execution. SQL files matching
`*.sql` are processed in sorted filename order within each configured directory,
so use names such as `01_create_tables.sql` and `02_seed_data.sql`.

!!! warning "Scripts can run again"
    Applying the workspace can execute enabled SQL scripts again. Make them
    safe to re-run and back up existing data before schema changes.

The dashboard provider determines the PostgreSQL connection configuration:
Superset uses the in-cluster setup, while Power BI uses the Azure PostgreSQL
integration. Have the administrator configure the corresponding connectivity,
credentials, and Kubernetes permissions.

## Runtime credentials and CoAL configuration

Schema initialization creates workspace-scoped Kubernetes resources in the
tenant namespace:

- Secret `<organization_id>-<workspace_id>`, containing
  `POSTGRES_USER_PASSWORD`.
- ConfigMap `<organization_id>-<workspace_id>-coal-config`, containing
  `coal-config.toml`.

The CoAL configuration references `env.POSTGRES_USER_PASSWORD` rather than
embedding the password directly. Kubernetes encodes Secret data in base64;
base64 is **not encryption**, so restrict access appropriately.

Existing workspace Secrets or ConfigMaps may be retained rather than recreated.
Do not expect reapplying a manifest to rotate stored credentials automatically.
The [destroy macro](../tutorial/destroy.md) targets these resources together with
the tracked PostgreSQL schema during workspace cleanup.
