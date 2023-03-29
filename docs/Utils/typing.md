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

- `%deploy%<JMESPath Query>` : This will apply the given JMESPath query to the deploy config file and send the result as an argument instead.
- `%platform%<JMESPath Query>` : Same as above but will get applied to the platform config file.
- `%workdir[File/Path]%<JMESPath Query>` : This syntax will apply the JMESPath query to the give file in the working directory

### Example use
Using the previously defined command and the following example config files
```yaml
# Deploy
solution_id: "MySolution"
```

```yaml
# Platform
organization_id: "MyOrganization"
```

We can except the following results :
```bash
my_call %deploy%solution_id
# The value of my arg is :
# MySolution
my_call %platform%*
# The value of my arg is :
# ['MyOrganization']
```

For more information on the JMESPath syntax I invite you to check the following website : [JMESPath.org](https://jmespath.org)


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
