# Deploy Superset dashboards

Start with a [configured deployment](deploy.md) initialized using:

```bash
babylon init azure superset
```

The cloud provider can also be `kob`. Your platform administrator must configure
Superset connectivity and an identity allowed to import assets and enable
embedding.

## Add dashboard exports

Export configured dashboards from Superset as ZIP files and place them under
`project/dashboard/superset/`, for example `dashboard_satisfaction.zip`.
Do not unpack them in the project.

Enable the dashboard sidecar in `project/Workspace_superset.yaml`. This fragment
belongs under `spec.sidecars`:

```yaml
dashboards:
  provider: superset
  create: true
  reports:
    - path: dashboard/superset
```

The report path is relative to the deployment directory (`project/`).
Ensure the [PostgreSQL sidecar](../guides/postgres.md) matches the source data
expected by the dashboards.

## Configure web app charts

Adapt `spec.payload.additionalData.webapp.charts` to your own dashboards.
For a dashboard titled **QA - Dashboard - Satisfaction**, an example is:

```yaml
charts:
  supersetDomain: "https://superset-{{cluster_name}}.{{domain_zone}}"
  dashboards:
    - id: "{{qadashboardsatisfaction}}"
      width: 100%
      filters:
        - id: <your-native-filter-id>
          operator: ==
          column: Simulation_run
          value: lastRunId
  dashboardView:
    - id: "{{qadashboardsatisfaction}}"
      title:
        en: Customers overview
        fr: Aperçu des clients
```

Dashboard template keys are made from the original Superset dashboard title by
lowercasing it and removing characters outside `a-z` and `0-9`.
Thus **QA - Dashboard - Scenario View** becomes `qadashboardscenarioview`.
Use names that produce distinct, nonempty keys. Native filter IDs must be
obtained from your dashboard configuration, not copied from the sample.

During deployment Babylon prefixes asset display names with the workspace ID
(for example `[w-abc123] My Dashboard`). This scopes imported assets to the
workspace; the prefix is excluded when calculating template keys.

## Apply and verify

```bash
babylon apply --include workspace project/
babylon namespace show-state local
```

The organization and solution must already exist in the active state.
Babylon imports the assets, enables embedding, records dashboard UUIDs in
[state](../guides/state.md#dashboard-identifiers), and renders the workspace
configuration with those UUIDs. Keep template expressions in the manifest
rather than hard-coding environment-specific UUIDs.

Verify dashboard access in the web app with the intended user roles. If
embedding or visibility fails, ask the platform administrator to check Superset
permissions and Keycloak role mapping rather than granting broader access to
all users.
