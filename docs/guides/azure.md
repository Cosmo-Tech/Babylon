# Azure deployment requirements

A platform administrator must first provision the Cosmo Tech platform and tenant.
Babylon deploys project resources against that platform; installing the CLI does
not create the platform or grant access.

## Separate API and Azure authentication

The current Cosmo Tech API authentication uses Keycloak credentials supplied by
the `babylon-config` Secret or the four
[API environment variables](../getting_started/configuration.md#environment-variables).
It does not use the older Azure app registration's `Platform.Admin` permission
as a substitute for Keycloak authentication.

Azure-backed web apps and Power BI integrations additionally need Azure
credentials and permissions. Confirm your subscription and identity with the
administrator before provisioning:

```bash
az login
az account show
az account set --subscription <subscription-id>
```

## Permissions depend on the operation

- Resource deployment needs the relevant resource-group permissions
  (the earlier guide used **Contributor**).
- Creating web app registrations or enterprise applications needs suitable
  Entra application-management permissions.
- Resolving group ACLs needs the appropriate Microsoft Graph access.
- Power BI publishing and workspace permissions have their own licensing and
  tenant requirements; see the [Power BI example](../examples/powerbi.md).
- Kubernetes Secret access and job execution are controlled by Kubernetes RBAC,
  not by an Azure resource-group role alone.

The former Azure setup guide listed broad Microsoft Graph grants such as
`Application.ReadWrite.All` and `Group.ReadWrite.All` for a single Babylon app.
Do not grant all of them automatically: have an administrator choose the least
privilege required for your deployment and consent policy.

Consult Microsoft's guidance on
[application configuration](https://learn.microsoft.com/en-us/entra/identity-platform/msal-client-application-configuration)
and [OAuth authorization flows](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow),
plus the selected
[Terraform web app module](https://github.com/Cosmo-Tech/terraform-webapp)
release's requirements.
