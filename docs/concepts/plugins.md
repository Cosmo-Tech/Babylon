# Concerning plugins

Now, where to begin? Ah, yes. "Concerning plugins". Plugins have been added as a part of babylon before the 1.0. Quite
content to ignore and be ignored by the world of the other commands. Babylon being, after all, full of commands beyond
count. Plugins must seem of little importance, being neither renowned as great commands, nor being part of the roadmap.
... In fact, it has been remarked by some that plugins only real usage if for other developers. A rather unfair
observation as they have also been developed by the maintainers of the repo, and made an integral part of Babylon. But
where their hearts truly lies is in peace and easiness of development.

## How to create a plugin

A plugin folder follows a simple basic format:

```text
- __init__.py
- requirements.txt
- plugin_config.yaml
```

The `__init__.py` file contains at minima a click command named after the plugin (for example: `MyPlugin`)

```python
import click


@click.command()
@wrapcontext()
def MyPlugin():
    print("This is my awesome Plugin")
```

The `requirements.txt` contains all specific requirements necessary for the plugin, in case of conflict with the plugins
required by Babylon they won't be installed

The `plugin_config.yaml` contains some information about the plugin, as of now it is relatively bare

```yaml
plugin_name: MyPlugin
```

You can see that the name of the command in the `__init__.py` and the `plugin_name` in the `plugin_config.yaml` are
identical. It is by design, as the parameter `plugin_name` is used by babylon to find the command in the `__init__.py`
to make it an available command.


## Interact with a plugin

You can make use of the group of commands `babylon plugin` to add/remove or activate/deactivate a plugin.

Adding a plugin makes it known to babylon, before its folder are ignored and any change you made to them would have no
effect, removing a plugin won't delete your folder, it will only unlink them from babylon at the configuration level.

Activating a plugin will make it available in the cli, be careful, a plugin with the name of a babylon core command
won't be usable even if not refused when adding it. This is by design, core commands are always first. Deactivating a
plugin won't remove it, it will just make the command unavailable to the cli, reactivating it will make it available
once again.
