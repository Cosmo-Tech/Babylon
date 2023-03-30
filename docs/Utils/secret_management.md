# Secret management

Babylon allows encrypting and decrypting files using a symmetrical encrypting algorithm.

A `.secrets.yaml.encrypt` file exists in your current working directory and will hold sensitive information such as passwords, tokens, etc.  
This file is encrypted in a way that it can be shared between users, as long as they have the same `secret.key`. 

!!! warning "Good practice"
    **Be careful and keep that secret securely !**  
    We encourage teams to share their `secret.key` using a key vault or a password manager such as **Keepass**.  
    Without it, you won't be able to decrypt your files in the future !

## Commands 

### `babylon config set-variable secrets [key] [value]`
Using this command you can set a variable inside the `.secrets.yaml.encrypt` file.  
If you the key has dots in it, it will be interpreted as a nested key.  

#### Example
`babylon config set-variable secrets github.token hello-world`  
Will result in the following file:  
```yaml
github:
    token: hello-world
```

### `babylon config get-variable secrets [key] [value]`
Using this command you can get a variable inside the `.secrets.yaml.encrypt` file.  
If you the key has dots in it, it will be interpreted as a nested key.  

#### Example
`babylon config get-variable secrets github.token`  
Will print the following value
```bash
{"value": "hello-world"}
```
`babylon config get-variable secrets github`  
Will print the following value
```bash
{"value": {"token": "hello-world"}}
```

### Query Types
Some commands allow the use of `QueryType` parameters, when using this type you can target the `.secrets.yaml.encrypt` file using the `%secrets%` prefix.

## Additional secret storage

You can create additional `.encrypt` files in your working directory and decrypt/encrypt them using the following commands.  
- `babylon working-dir encrypt-file [file]`  
- `babylon working-dir decrypt-file [file]`

Commands can use those values using the `QueryType` syntax with `%workdir[my_file.yaml.encrypt]%` prefix.