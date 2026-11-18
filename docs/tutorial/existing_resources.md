# Use an existing organization and solution

Use the API commands when creating an object under an existing shared parent.
Unlike the deployment macros, these commands take explicit parent identifiers.
Configure your [namespace and credentials](../getting_started/configuration.md)
before starting.

!!! warning "Do not use the old metadata selectors"
    The current `apply` implementation does not read
    `metadata.selector.organization_id` or `metadata.selector.solution_id`.
    Adding those fields to a manifest does not select an existing parent.
    This replaces the selector-based instructions from the separate end-user
    documentation.

## Create a solution in an existing organization

Prepare `solution-payload.yaml` as the **API payload only**, using the target
platform's solution schema. Do not wrap it in the macro's `kind`, `namespace`,
or `spec` sections.

```bash
babylon api solutions list --oid <organization_id>
babylon api solutions create --oid <organization_id> solution-payload.yaml
```

Keep the resulting solution ID for the workspace creation step.

## Create a workspace in an existing organization and solution

For example, `workspace-payload.yaml` can start with:

```yaml
key: myworkspace
name: My workspace
description: Workspace using an existing solution
solution: {}
security:
  default: none
  accessControlList:
    - id: admin@example.com
      role: admin
```

Add any settings required by your platform and web application, then run:

```bash
babylon api workspaces create --oid <organization_id> --sid <solution_id> workspace-payload.yaml
babylon api workspaces get --oid <organization_id> --wid <workspace_id> -o yaml
```

The solution is selected with `--sid`; API payload files do not use the macro's
`{{...}}` variable substitution.

!!! note "API calls are not deployments"
    These commands create API objects only. They do not provision macro sidecars
    or adopt shared parents into a new managed deployment. Do not assume that
    `apply` or `destroy` will manage resources created independently through the
    API. Use explicit API commands for their subsequent lifecycle.

## Other API resources

Datasets, runners, and runs are also managed through the API command tree:

```bash
babylon api datasets create --oid <organization_id> --wid <workspace_id> dataset-payload.yaml
babylon api runners create --oid <organization_id> --sid <solution_id> --wid <workspace_id> runner-payload.yaml
babylon api runs list --oid <organization_id> --wid <workspace_id> --rid <runner_id>
```

Consult the [generated CLI reference](../references/cli.md) and your target API
schema for payload requirements. The older `kind: Dataset` and `kind: Runner`
macro examples are not supported by `apply`.
