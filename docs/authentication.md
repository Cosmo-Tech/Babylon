# Changes about authentication in Babylon

There are now two ways of authenticating with Babylon and az cli is no longer required. As usual, you should have a clean working dir with all needed configurations files. Don't forget to use the `babylon working-dir complete` and `babylon config init` commands if needed. Babylon will always try to retrieve cached credentials in the secret file: if any, it will be used to get a valid token 


## Authentication with environment variables

Requires the following environment variables:

`AZURE_CLIENT_ID`
`AZURE_TENANT_ID`
`AZURE_CLIENT_SECRET`

This values should come from an Azure app registration


## Authentication with interactive browser credential

The prefered way to authenticate to Azure services, it launches the system default browser to interactively authenticate a user
