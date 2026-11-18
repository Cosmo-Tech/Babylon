# Update access controls

Use the same namespace and deployment files as the original deployment.
Losing or changing state can cause `apply` to create resources rather than update
them. Verify the [state](../guides/state.md) first:

```bash
babylon namespace use -c my-project -t my-tenant
babylon namespace get-contexts
babylon namespace show-state local
```

## Share security across API objects

The generated organization, solution, and workspace manifests reference the
same `security` variable. To grant Alice editor access and Bob viewer access,
edit that value in `variables.yaml`, preserving the existing administrators:

```yaml
security:
  default: none
  accessControlList:
    - id: admin@example.com
      role: admin
    - id: alice@example.com
      role: editor
    - id: bob@example.com
      role: viewer
```

Apply the affected resource kinds:

```bash
babylon apply --include organization --include solution --include workspace project/
```

!!! warning "Review the complete desired ACL"
    Security synchronization can remove entries omitted from the desired
    configuration. Preserve required administrators and review every affected
    object. Including a workspace also processes its configured sidecars; this
    is not a payload-only update.

## Use different security for each object

Define `organization_security`, `solution_security`, and `workspace_security` in
the variable file when their ACLs must differ. Then change each corresponding
manifest's `spec.payload.security` to reference its own value, for example:

```yaml
security: {{workspace_security}}
```

Defining these variable names alone has no effect while the manifests still
reference `{{security}}`.

Power BI workspace permissions are separate from Cosmo Tech API security; see
the [Power BI example](powerbi.md#permissions-and-prerequisites).
