import logging

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")


class AzurePowerBIWorkspaceUserService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def add(self, workspace_id: str, right: str, type: str, email: str):
        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        identifier = email

        if not workspace_id or not identifier:
            logger.error("  [bold red]✘[/bold red] Missing workspace ID or identifier for Power BI permission update")
            return None
        
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        body = {
            "identifier": identifier,
            "groupUserAccessRight": right,
            "principalType": type,
        }
        response = oauth_request(url_users, self.powerbi_token, json=body, type="POST")
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to add user [cyan]{identifier}[/cyan] to Power BI workspace")
            return None
        logger.info(f"  [bold green]✔[/bold green] {type} [cyan]{identifier}[/cyan] successfully added to Power BI workspace")

    def delete(self, workspace_id, force_validation: bool, email: str):
        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users/{email}"
        if not force_validation and not confirm_deletion("user", email):
            return None
        response = oauth_request(url_users, self.powerbi_token, type="DELETE")
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete user [cyan]{email}[/cyan] from Power BI workspace")
            return None
        logger.info(f"  [bold green]✔[/bold green] User [cyan]{email}[/cyan] successfully removed from Power BI workspace")

    def get_all(self, workspace_id: str):
        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        response = oauth_request(url_users, self.powerbi_token)
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to retrieve users for workspace [cyan]{workspace_id}[/cyan]")
            return None
        output_data = response.json().get("value")
        return output_data

    def update(self, workspace_id: str, right: str, type: str, email: str):
        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        body = {
            "identifier": email,
            "groupUserAccessRight": right,
            "principalType": type,
        }
        response = oauth_request(url_users, self.powerbi_token, json=body, type="PUT")
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to update user [cyan]{email}[/cyan] in Power BI workspace")
            return None
        logger.info(f"  [bold green]✔[/bold green] User [cyan]{email}[/cyan] successfully updated in Power BI workspace")
        return response