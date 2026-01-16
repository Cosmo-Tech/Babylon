import pathlib

BABYLON_PATH = list(pathlib.Path(__file__).parents)[1]
ORIGINAL_TEMPLATE_FOLDER_PATH = BABYLON_PATH / "templates"
ORIGINAL_CONFIG_FOLDER_PATH = pathlib.Path().home() / ".config" / "cosmotech" / "babylon"
API_REQUEST_MESSAGE = "  [dim]→ Sending request to API...[/dim]"
