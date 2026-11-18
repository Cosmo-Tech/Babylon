# Deploy a project

## Prepare a working directory

After [installing](../getting_started/installation.md) and
[configuring](../getting_started/configuration.md) Babylon:

```bash
mkdir my-deployment
cd my-deployment
babylon namespace use -c my-project -t my-tenant
babylon init azure superset
```

--8<-- "docs/partials/project_tree.md"

Keep `variables.yaml` next to `project/`, not inside it.

## Customize the variables

Edit the generated file rather than replacing it with this excerpt. Every
template variable referenced by your manifests must be defined:

```yaml
organization_name: Example organization
solution_name: Example solution
solution_key: examplesolution
solution_description: Example simulator
simulator_repository: my-tenant/my-simulator
simulator_version: "1.0.0"
workspace_name: Example workspace
workspace_key: exampleworkspace
workspace_description: Example deployment
remote: true
security:
  default: none
  accessControlList:
    - id: admin@example.com
      role: admin
    - id: editor@example.com
      role: editor
    - id: viewer@example.com
      role: viewer
```

Use the simulator's actual run templates and parameters in `Solution.yaml`.
Replace sample users with authorized identities. By default, the generated
organization, solution, and workspace manifests share the `security` variable.

For web app deployment, also review `cloud_provider`, `cluster_name`,
`domain_zone`, `tenant`, `webapp_name`, and `tf_webapp_version`. Azure additionally
needs the intended subscription and Entra tenant identifiers.
The YAML `tenant` value must match the namespace selected for this deployment.

The generated manifest uses state references such as
`{{services['api.organization_id']}}`; do not replace them with a sample ID.

## Choose the resources to deploy

The scaffold contains a simulator build, web app, PostgreSQL jobs, and
Brewery-specific dashboard settings. These are examples to review, not a
ready-to-run deployment for every platform.

- If the simulator image already exists, skip `Build` during deployment.
- If no web app is needed, skip `Webapp`.
- Dashboard imports are disabled by default. Configure
  [Superset](superset.md) or [Power BI](powerbi.md) before enabling them.
- If you are not importing dashboards, remove or adapt sample chart references
  in the workspace payload so it does not point at nonexistent reports.
- Review the sample SQL before enabling it; see [PostgreSQL sidecars](../guides/postgres.md).

For an existing image with no web app:

```bash
babylon apply --exclude build --exclude webapp project/
```

For the full reviewed project, including a Modeling API build:

```bash
babylon apply project/
```

Custom variable filenames must be supplied explicitly:

```bash
babylon apply --var-file deployment.yaml project/
```

## Inspect and maintain the deployment

```bash
babylon namespace get-contexts
babylon namespace show-state local
babylon api workspaces get --oid <organization_id> --wid <workspace_id> -o json
```

Keep the working directory and [state](../guides/state.md) for subsequent
updates. See [access-control updates](update.md) or
[safe destruction](../tutorial/destroy.md) for the next steps.
