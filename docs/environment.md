# About the environment

An environment is a combination of 3 part : 
- A platform
- A solution
- A deployment

## Solution

A solution is the ensemble of files you will need to have a running simulator on the cloud.

```text
Solution
├── ...
└── API
    └── API_FILES_HERE
```

### API

This is a folder containing the different files you will want to send to the api

For example:

- Solution.yaml
- Workspace.json

## Deployment

A deployment is the link between a solution and a platform

### deploy.yaml

This is a yaml file containing a list of key-values used to identify the deployment of a solution in the platform

```yaml
--8<-- "Babylon/templates/ConfigTemplate/deployments/deploy.yaml"
```

## Platform

A platform is a cloud where you deployed an API

### platform.yaml

This is a yaml file containing a list of key values used to identify the platform to connect

```yaml
--8<-- "Babylon/templates/ConfigTemplate/platforms/platform.yaml"
```
