# Macro commands

## Concept

The idea of a macro command is to allow the developer to do a script of commands inside of Babylon instead of using bash or other technologies.

To make this possible 2 elements are required : 
- A way to call a command inside another command
- A way for commands to exchange information between their runs


## Helpers

The following function exists to help you run other commands inside a command.

::: Babylon.utils.command_helper.run_command
    handler: python
    options:
       separate_signature: true
       show_root_heading: true
       show_root_full_path: false
       show_source: false
       line_length: 40
       docstring_style: sphinx
       docstring_section_style: list
       heading_level: 3

## Return type

The following class was defined as a response type for commands allowing returns to keep information

::: Babylon.utils.response.CommandResponse
    handler: python
    options:
       separate_signature: true
       show_root_heading: true
       show_root_full_path: false
       show_source: false
       line_length: 40
       docstring_section_style: list
       docstring_style: sphinx
       heading_level: 3