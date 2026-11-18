# Babylon CLI ![VERSION](https://img.shields.io/badge/VERSION-2e303e?style=for-the-badge)

[![Cosmotech](https://img.shields.io/badge/Cosmotech-ffb039?style=for-the-badge&logoColor=black)](https://cosmotech.com/)

Babylon is the command-line interface for provisioning, configuring, and managing
Cosmo Tech solutions and platforms. Use high-level macros to scaffold, deploy,
update, and destroy a project, or the API commands for individual resources.

User guides and developer references now live together on this site.

## Start here

- [Install Babylon](getting_started/installation.md) in a Python virtual environment.
- [Configure authentication and a namespace](getting_started/configuration.md).
- Follow the [workspace deployment tutorial](tutorial/deploy.md) and
  [complete deployment example](examples/deploy.md).
- Add [Superset](examples/superset.md) or [Power BI](examples/powerbi.md) dashboards.
- Consult the [generated CLI reference](references/cli.md) for supported commands
  and options.

## Typical workflow

```bash
babylon namespace use -c my-project -t my-tenant
babylon init azure superset
# Review variables.yaml and the generated manifests before deploying.
babylon apply project/
```

![Babylon CLI demo](assets/img/babylon-demo.gif)

Read about [deployment state](guides/state.md) before updating or
[destroying resources](tutorial/destroy.md). Contributors can find
[development guidance](concepts/contribute.md) and
[documentation build instructions and provenance](concepts/documentation.md).
