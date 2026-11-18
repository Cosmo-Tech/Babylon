# Deploy Power BI dashboards

Power BI is integrated through `init`, `apply`, and `destroy`. There is no
standalone `babylon powerbi` command in the public CLI.

## Permissions and prerequisites

In addition to the [Azure requirements](../guides/azure.md), arrange:

- A Power BI license/capacity and tenant settings that allow workspace creation
  and report publishing.
- An Azure identity authorized to create the required web app registrations and
  enterprise applications, when using that integration.
- Permission to manage the target Power BI workspace/group and resolve any
  groups used in its ACL.
- Access to the PostgreSQL data source used by the reports.

Ask your administrators to grant the least privilege required by the operations.
The source guide used the Entra **Application Administrator** role for app
creation and required group ownership; verify the appropriate assignment for
your organization's policies.

## Prepare reports

Initialize a [deployment](deploy.md) with the Power BI provider:

```bash
babylon init azure powerbi
```

Place the report files in `project/dashboard/powerbi/`, for example
`brewery_dashboard.pbix`. Prepare the reports in Power BI Desktop using
parameterized data sources so that they can move between environments.

The current template targets PostgreSQL, not the ADX data sources in the older
v4 guide. Match the report parameter names exactly: the scaffold supplies
`Server` and `Database`, and Babylon adds a `Schema` parameter from the workspace
state if none is supplied explicitly. Use the actual host and database for
your tenant.

Enable the following sidecar under `spec.sidecars` in
`project/Workspace_powerbi.yaml`, adapting its connection values:

```yaml
dashboards:
  provider: powerbi
  create: true
  name: "{{powerbi_workspace_name}}"
  permissions: {{powerbi_permissions}}
  reports:
    - path: dashboard/powerbi
      parameters:
        - id: Server
          value: "csm-{{cluster_name}}.postgres.database.azure.com"
        - id: Database
          value: "tenant-{{tenant}}"
```

Report paths are relative to `project/`.

## Configure permissions

Edit the generated variable file:

```yaml
powerbi_workspace_name: Example Power BI workspace
powerbi_permissions:
  - identifier: admin@example.com
    rights: Admin
    type: User
  - identifier: Delivery Team
    rights: Member
    type: Group
powerbi_app_deploy: true
```

Groups can be resolved by their Entra display names. Ensure names resolve to the
intended group. These permissions are independent of the Cosmo Tech API object's
`security` ACL. When the Terraform web app creates a Power BI app registration,
Babylon can add its service principal to the workspace permissions.

## Configure web app charts

Adapt the `charts` section under
`spec.payload.additionalData.webapp`:

```yaml
charts:
  workspaceId: "{{powerbi['workspace_id']}}"
  logInWithUserCredentials: false
  useWebappTheme: true
  dashboardsView:
    - title:
        en: Customers overview
        fr: Aperçu des clients
      reportId: "{{powerbi['reports']['brewery_dashboard']}}"
      pageName:
        en: <your-report-page-id>
        fr: <your-report-page-id>
      settings:
        filterPaneEnabled: false
        navContentPaneEnabled: false
      dynamicFilters:
        - table: "{{services['postgres.schema_name']}} cosmotech_satisfaction"
          column: Simulation_run
          values: lastRunId
```

Use page IDs, table names, and columns from your report. For auto-discovered PBIX
files the report key is derived from the basename, normalized to lowercase with
non-alphanumeric runs replaced by underscores: `Brewery Dashboard.pbix` becomes
`brewery_dashboard`.

## Deploy and maintain

After reviewing the full project's configuration:

```bash
babylon apply project/
```

For later dashboard updates on an existing managed deployment:

```bash
babylon apply --include workspace project/
```

Babylon publishes reports, takes dataset ownership, updates parameters and
credentials, synchronizes permissions, and stores the report/workspace IDs in
[state](../guides/state.md#dashboard-identifiers). Keep template references
instead of pasting environment-specific IDs into the manifest.

See [destruction](../tutorial/destroy.md) before removing a deployment: workspace
cleanup also targets its tracked Power BI assets.
