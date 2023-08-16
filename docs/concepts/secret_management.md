# Secret management

Babylon use a [Vault](https://www.vaultproject.io/) service for all secrets and provides a group of commands that can be used.

Vault is a tool for securely accessing secrets. A secret is anything that you want to tightly control access to, such as API keys, passwords, certificates, and more. Vault provides a unified interface to any secret, while providing tight access control and recording a detailed audit log.

!!! secrets
    ```bash
    babylon hvac set [scope] [key] [value]
    ```

    Scope availables:

    * `babylon`
    * `global`
    * `platform`
    * `project`
    * `users`

Example,

* Set new secret in global scope
```bash
babylon hvac set global github token hello-world 
```