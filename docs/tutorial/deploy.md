# Deploy a Cosmo Tech workspace

Complete [configuration](../getting_started/configuration.md) first. This
tutorial explains the manifests; the [deployment example](../examples/deploy.md)
combines them into a project.

## Scaffold the project

Run the following in a dedicated working directory:

```bash
babylon namespace use -c my-project -t my-tenant
babylon init azure superset
```

Choose `azure` or `kob` for the cloud provider, and `superset` or `powerbi` for the
dashboard provider. `init` generates provider-specific manifests, SQL examples,
and a sibling `variables.yaml`, and clones the Terraform web app module.

--8<-- "docs/partials/project_tree.md"

For Power BI, the workspace manifest and dashboard directory are named
`Workspace_powerbi.yaml` and `dashboard/powerbi/` instead.
Custom names can be supplied when scaffolding:

```bash
babylon init --project-folder deployment --variables-file deployment.yaml azure superset
```

Do not run `init` over customized manifests without a backup. Its templates and
the Terraform checkout are scaffolding, not a merge mechanism.

## Understand the manifests

The root YAML files in the deployment directory define resources. `kind` is
case-sensitive: `Build`, `Organization`, `Solution`, `Workspace`, and `Webapp`
are handled by `apply`. Datasets and runners use the API commands, not these
macros.

### Organization

This example is included directly from the template shipped with Babylon:

```yaml
--8<-- "Babylon/templates/working_dir/.templates/yaml/Organization.yaml"
```

`namespace.remote` controls whether state is persisted in Kubernetes as well as
locally. `spec.payload` contains the API object's configuration.

Template expressions are resolved from `variables.yaml`; for example
`"{{organization_name}}"` is a string and `{{security}}` inserts a structured
value. Previously deployed resource IDs are available through flattened state
keys such as `{{services['api.organization_id']}}`.

### Solution

The generated `Solution.yaml` describes the simulator repository, image version,
run templates, parameters, and security. Review those values against the
simulator you intend to deploy; the Brewery sample definitions are not generic
defaults for every solution.

When creating resources from scratch, Babylon records the organization ID in
state and uses it when creating the solution.

### Workspace and sidecars

`Workspace_superset.yaml` or `Workspace_powerbi.yaml` defines the workspace's API
payload and the sidecar resources under `spec.sidecars`.

- `postgres.schema.create` enables PostgreSQL schema initialization.
- `postgres.schema.jobs` selects Kubernetes job templates.
- `postgres.schema.scripts` controls execution of project SQL scripts.
- `dashboards` selects the provider, enables imports, and identifies report files.

The workspace payload references `{{services['api.solution_id']}}`. Configure its
web app settings under `spec.payload.additionalData.webapp`, including dashboard
layout and filters. See [PostgreSQL sidecars](../guides/postgres.md) and the
[dashboard examples](../examples/index.md).

### Web app

`Webapp.yaml` supplies the provider-specific inputs for
[terraform-webapp](https://github.com/Cosmo-Tech/terraform-webapp), including the
cluster, domain, tenant, organization, and web app name. Use `domain_zone` from
the current generated template, not the older `cluster_domain` field.

`init` can select a module release using `--tf-webapp-version`. Also review
`tf_webapp_version` in the generated variable file; that value is used during
deployment. Consult the module's documentation for its own prerequisites.

### Simulator build

`Build.yaml` uses the Modeling API to build a simulator from
`project_archive_url`, optionally publishing its image. Supported project
locations include local `file:///` folders or archives and Git references such
as `git+https://github.com/<organization>/<repository>.git@<tag>`.

If your tenant has no Modeling API, or you already have the required simulator
image, skip this resource when applying.

## Deploy and update

Review every generated file and replace the sample values before running:

```bash
babylon apply project/
```

Babylon processes builds, organizations, solutions, web apps, then workspaces.
It uses state to update existing resources on subsequent deployments. Preserve
the same context, tenant, working directory, and variable files when updating.

The default variable file is `variables.yaml` in the current working directory,
not inside `project/`. Multiple files can be supplied explicitly, but their keys
must be disjoint; duplicate keys are rejected rather than overridden.

```bash
babylon apply --var-file common.yaml --var-file tenant.yaml project/
```

To select only certain resource kinds, repeat the selection option:

```bash
babylon apply --include organization --include solution project/
babylon apply --exclude build project/
```

Do not combine `--include` and `--exclude`. A selection does not create missing
dependencies: for example, workspace deployment still needs the target
organization and solution. Use the [existing-resources tutorial](existing_resources.md)
for API-only operations on shared resources.

See [deployment state](../guides/state.md) before moving or cleaning up a project.
