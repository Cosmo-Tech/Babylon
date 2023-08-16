# Specific types

## QueryType

This type adds a capacity to easily use file content as parameter to function.

### Example in a command

The following code is an example of use of the type:
```python
from Babylon.utils.typing import QueryType
import click

@click.command()
@click.argument("my_arg", type=QueryType())
def my_call(my_arg):
    print("The value of my arg is :")
    print(my_arg)
```

### Usage
The `QueryType` accepts the following syntaxes :

- `%resource%<key_name>` : This will retrieve the given key name from the resource config file and send the result as an argument instead.

### Example use
Using the previously defined command and the following example config files
```yaml
# config file api resource
solution_id: "MySolution"
```

We can accept the following results :
```bash
my_call %api%solution_id
# The value of my arg is :
# MySolution
```

::: Babylon.utils.typing.QueryType
    handler: python
    options:
       show_root_heading: true
       show_root_full_path: true
       show_source: false
       line_length: 40
       docstring_style: sphinx
       heading_level: 3
       members:
         - shell_complete
         - convert
