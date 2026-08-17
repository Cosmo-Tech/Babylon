import logging

from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzurePowerBIWorkspaceService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.powerbi_token = powerbi_token
        self.state = state

    def create(self, name: str):
        """Create a new Power BI workspace."""

        url_groups = "https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True"
        response = oauth_request(
            url=url_groups,
            access_token=self.powerbi_token,
            json={"name": name},
            type="POST",
        )
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to create Power BI workspace [cyan]{name}[/cyan]")
            return None
        output_data = response.json()
        return output_data

    def delete(self, workspace_id: str, force_validation: bool):
        """Delete a Power BI workspace after optional confirmation."""

        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        if not workspace_id:
            logger.error("  [bold red]✘[/bold red] Missing workspace ID for Power BI deletion")
            return CommandResponse.fail()
        
        if not force_validation and not confirm_deletion("Power Bi Workspace", workspace_id):
            logger.info(f"  [dim]→ Deletion cancelled for workspace [cyan]{workspace_id}[/cyan][/dim]")
            return CommandResponse.fail()

        logger.info(f"  [dim]→ Deleting Power BI workspace [cyan]{workspace_id}[/cyan]...[/dim]")
        url_delete = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        response = oauth_request(url=url_delete, access_token=self.powerbi_token, type="DELETE")

        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete Power BI workspace [cyan]{workspace_id}[/cyan]")
            return CommandResponse.fail()
        logger.info(f"  [bold green]✔[/bold green] Power BI workspace [cyan]{workspace_id}[/cyan] successfully deleted")
        return response

    def get_all(self):
        """Retrieve all Power BI workspaces accessible by the authenticated user."""

        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        response = oauth_request(url=url_groups, access_token=self.powerbi_token)
        if response is None:
            logger.warning("  [bold red]✘[/bold red] Either workspace name list is empty or you are not allowed to access the PowerBI service")
            return None
        output_data = response.json().get("value")
        return output_data

    def get_current(self):
        """Retrieve details for the current active Power BI workspace stored in state."""

        workspace_id = self.state.get("powerbi", {}).get("workspace", {}).get("id")
        if not workspace_id:
            logger.error("  [bold red]✘[/bold red] No active Power BI workspace ID found in state")
            return None

        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        params = {"$filter": f"id eq '{workspace_id}'"}
        response = oauth_request(url_groups, self.powerbi_token, params=params)
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to request details for Power BI workspace [cyan]{workspace_id}[/cyan]")
            return None
        workspace_data = response.json().get("value")
        if not workspace_data:
            logger.error(f"  [bold red]✘[/bold red] Power BI workspace [cyan]{workspace_id}[/cyan] not found")
            return None
        return workspace_data
