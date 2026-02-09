from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, OrganizationApi
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest
from yaml import safe_load

from Babylon.utils import API_REQUEST_MESSAGE
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_organization_api_instance(config: dict, keycloak_token: str) -> OrganizationApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return OrganizationApi(api_client)


@group()
def organizations():
    """Organization - Cosmotech API"""
    pass


@organizations.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("payload_file", type=Path(exists=True))
def create(config: dict, keycloak_token: str, payload_file) -> CommandResponse:
    """
    Create an organization using a YAML payload file.
    """
    # Load and parse the payload
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    # Initialize API
    organization_create_request = OrganizationCreateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        organization = api_instance.create_organization(organization_create_request)

        if not organization:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(
            f"  [bold green]✔[/bold green] Organization [bold cyan]{organization.id}[/bold cyan] successfully created"
        )
        return CommandResponse.success(organization.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@organizations.command()
@injectcontext()
@pass_keycloak_token()
@option("-O", "--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """
    Delete an organization by ID
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        # API Execution
        logger.info(API_REQUEST_MESSAGE)
        api_instance.delete_organization(organization_id)
        logger.info(
            f"  [bold green]✔[/bold green] Organization [bold red]{organization_id}[/bold red] successfully deleted"
        )
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@organizations.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
def list_organizations(config: dict, keycloak_token: str) -> CommandResponse:
    """
    List all organizations
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        organizations = api_instance.list_organizations()
        count = len(organizations)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] organization(s) retrieved successfully")
        data_list = [org.model_dump() for org in organizations]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@organizations.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("-O", "--oid", "organization_id", required=True, type=str, help="Organization ID")
def get(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Get organization"""
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        organization = api_instance.get_organization(organization_id=organization_id)
        logger.info(f"  [green]✔[/green] Organization [bold cyan]{organization.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success({organization.id: organization.model_dump()})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Organization Failed Reason: {e}")
        return CommandResponse.fail()


@organizations.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("-O", "--oid", "organization_id", required=True, type=str, help="Organization ID")
@argument("payload_file", type=Path(exists=True))
def update(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    """
    Update organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_update_request = OrganizationUpdateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        updated = api_instance.update_organization(
            organization_id=organization_id, organization_update_request=organization_update_request
        )
        logger.info(f"  [green]✔[/green] Organization [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Organization Failed Reason: {e}")
        return CommandResponse.fail()
