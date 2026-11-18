# Delivery Brewery

The [delivery-brewery repository](https://github.com/Cosmo-Tech/delivery-brewery)
provides a standard Babylon project for deploying a Brewery solution. Access
may require organization membership.

Use its project files and README as the starting point, then:

1. Select the intended [cluster and Babylon namespace](../getting_started/configuration.md).
2. Review the project variables, simulator version, ACLs, and provider settings.
3. Configure [Superset](superset.md) or [Power BI](powerbi.md) reports as needed.
4. Follow the [deployment example](deploy.md), using the repository's deployment
   directory and variable filename.
5. Preserve the [state](../guides/state.md) for future updates and cleanup.

Do not run `babylon init` over an existing customized project without reviewing
which files it will replace.

The former Brewery walkthrough using `babylon config`, `babylon azure`,
`babylon hvac`, ADX, and standalone Power BI commands described an older CLI.
Use the macro workflow and the [current CLI reference](../references/cli.md)
instead; those older commands are not registered by this version.
