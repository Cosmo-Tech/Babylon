# About the environment

An environment is a combination of 2 parts :

- A working directory
- Configuration files

Simple access to the full environment can be made by using the singleton `Babylon.utils.environment.Environment`

## Working Directory

A working directory is the folder you will need to perform a babylon command.

It contains:
```text
├── .payload
├── adx
├── config
├── dtdl
└── powerbi
    ├── dashboard
    └── scenario
```


* **payload** (API request)

   This is a folder containing the different files you will want to send to API Cosmo Tech

* **adx** (Azure Data Explorer)

   This is a folder containing the different scripts you will want to send to ADX

* **dtdl** (Azure Digital Twins)

   This is a folder containing the different models you will want to send to ADT

* **powerbi** (PowerBI Workspace)

   This is a folder containing the different reports you will want to send to Worskpace PowerBI




## Configuration

All config files can be controlled by the group of commands:

```bash
babylon config [COMMANDS]
```
A configuration is the ensemble of files you will need to perform a babylon command in a specific context and platform.

You will find:

- `<context_id>`.`<platform_id>`.acr.yaml
- `<context_id>`.`<platform_id>`.adt.yaml
- `<context_id>`.`<platform_id>`.adx.yaml
- `<context_id>`.`<platform_id>`.app.yaml
- `<context_id>`.`<platform_id>`.api.yaml
- `<context_id>`.`<platform_id>`.azure.yaml
- `<context_id>`.`<platform_id>`.babylon.yaml
- `<context_id>`.`<platform_id>`.platform.yaml
- `<context_id>`.`<platform_id>`.powerbi.yaml
- `<context_id>`.`<platform_id>`.github.yaml
- `<context_id>`.`<platform_id>`.webpp.yaml
 

A config file is a yaml file containing a list of key-values used to identify resources.

For example: `<context_id>`.`<platform_id>`.acr.yaml

```yaml
--8<-- "Babylon/templates/config/acr.yaml"
```
