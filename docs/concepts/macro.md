# Macro commands

## Concept

The idea of a macro command is to allow the developer to do a script of commands inside of Babylon instead of using bash or other technologies.  
A macro is a command that can be used to chain other commands using the `Macro` class.

::: Babylon.utils.macro.Macro
    handler: python
    options:
       show_root_heading: true
       show_root_full_path: false
       show_source: false
       line_length: 40
       docstring_style: sphinx
       heading_level: 2
       members:
          - step
          - then
          - wait
          - dump
