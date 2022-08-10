# About the environment

An environment is a combination of 2 parts :

- A solution
- A configuration

## Solution

A solution is the ensemble of files you will need to have a running simulator on the cloud.

```text
Solution
├── ...
└── API
    └── API_FILES_HERE
```

More folders and file can be required and will be added in future version, don't hesitate to
use `babylon environment complete` to add missing elements of the solution.

### API

This is a folder containing the different files you will want to send to the api

For example:

- Solution.yaml
- Workspace.json

## Configuration

The configuration can be controlled by the group of commands `babylon config`

A configuration is the combination of a Deployment and a Platform.

### Deployment

A deployment is the link between a solution and a platform, it contains the ids required to access the instance of a
solution on a platform

#### deploy.yaml

This is a yaml file containing a list of key-values used to identify the deployment of a solution in the platform

```yaml
--8<-- "Babylon/templates/ConfigTemplate/deployments/deploy.yaml"
```

### Platform

A platform is a cloud where you deployed an API, you set the information required to access given platform

#### platform.yaml

This is a yaml file containing a list of key values used to identify the platform to connect

```yaml
--8<-- "Babylon/templates/ConfigTemplate/platforms/platform.yaml"
```
