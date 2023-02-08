# Secret management

Babylon allows encrypting and decrypting files using a symmetrical encrypting algorithm.

To start with encryption you can use th command `babylon working-dir encrypt-file` which will allow you to encrypt a full file.

## Commands 

=== "`babylon working-dir encrypt-file`"
    Using this command you can encrypt a file, if it is your first encryption a file `secret.key` will be generated at the same time  
    !!! warning "`secret.key`"
        Be careful and keep that secret securely !  
        Without it, you won't be able to decrypt your files in the future !

=== "QueryType"
    Some commands allow the use of `QueryType` parameters, when using this type you can target `.encrypt` files inside your working directory  
    Those files will be decrypted and made available for your queries.

## Secret Management

To manage secrets, you need to ensure that secrets values are inside a `.encrypt` file with the associated `secret.key`

Combining those allow to ensure that secret files could be exchanged between users, or even stored securely inside a VCS or a cloud storage.

But the responsibility of securing the `secret.key` will still be on the user side. If they loose it the encrypted files will become unreadable, and if it is made public, anyone could decrypt the files.