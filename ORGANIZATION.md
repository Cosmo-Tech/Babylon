# Organization of the repository

```text
Babylon                             : Core package
├── __init__.py                     : init file for the core package
├── main.py                         : Contains main function for the cli
├── version.py                      : Contains version number for the cli
├── groups                          : Groups package
│   ├── __init__.py                 : init file for the groups, contains list of all existing groups
│   └── <GROUP_NAME>                : Package for a given command group
│       ├── __init__.py             : init file for given command group, contains declaration of the click.group and add commands to it
│       └── commands                : Package for commands of a group
│           ├── __init__.py         : init file for the package, contains list of all commands in the package
│           └── <COMMAND_NAME>.py   : python file containing the code for the actual command
└── utils                           : Utils package
    ├── <UTIL_NAME>.py              : Util python file
    └── __init__.py                 : init file for the utils package
```