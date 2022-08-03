# About the environment

## Template

```text
Environment
├── deploy.yaml
├── platform.yaml
└── API
    └── API_FILES_HERE
```

### API

This is a folder containing the different files you will want to send to the api

For example:

- Solution.yaml
- Workspace.json

### deploy.yaml

This is a yaml file containing a list of key-values used to identify the deployment of a solution in the platform

```yaml
--8<-- "Babylon/templates/EnvironmentTemplate/deploy.yaml"
```

### platform.yaml

This is a yaml file containing a list of key values used to identify the platform to connect

```yaml
--8<-- "Babylon/templates/EnvironmentTemplate/platform.yaml"
```
