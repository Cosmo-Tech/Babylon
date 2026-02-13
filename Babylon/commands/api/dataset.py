from dataclasses import dataclass
from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, DatasetApi
from cosmotech_api.models.dataset_create_request import DatasetCreateRequest
from cosmotech_api.models.dataset_part_create_request import DatasetPartCreateRequest
from cosmotech_api.models.dataset_part_update_request import DatasetPartUpdateRequest
from cosmotech_api.models.dataset_update_request import DatasetUpdateRequest
from yaml import safe_load

from Babylon.utils import API_REQUEST_MESSAGE
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_dataset_api_instance(config: dict, keycloak_token: str) -> DatasetApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return DatasetApi(api_client)


@group()
def datasets():
    """Dataset - Cosmotech API"""
    pass


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def create(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file) -> CommandResponse:
    """
    Create a dataset using a YAML payload file.
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_create_request = DatasetCreateRequest.from_dict(payload)
    file_contents_list = [part["sourceName"] for part in payload["parts"]]
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        dataset = api_instance.create_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_create_request=dataset_create_request,
            files=file_contents_list,
        )
        if not dataset:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(f"  [bold green]✔[/bold green] Dataset [bold cyan]{dataset.id}[/bold cyan] successfully created")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def list_datasets(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """
    List all datasets
    """
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        datasets = api_instance.list_datasets(organization_id=organization_id, workspace_id=workspace_id)
        count = len(datasets)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Dataset(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in datasets]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def delete(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Delete a dataset by ID"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        api_instance.delete_dataset(organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id)
        logger.info(f"  [bold green]✔[/bold green] Dataset [bold red]{dataset_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get dataset"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        dataset = api_instance.get_dataset(organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id)
        logger.info(f"  [green]✔[/green] Dataset [bold cyan]{dataset.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Dataset Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@argument("payload_file", type=Path(exists=True))
def update(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Update dataset"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_update_request = DatasetUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        updated = api_instance.update_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_update_request=dataset_update_request,
            files=[part["sourceName"] for part in payload["parts"]],
        )
        logger.info(f"  [green]✔[/green] Dataset [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Dataset Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@argument("payload_file", type=Path(exists=True))
def create_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Create dataset part"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_part_create_request = DatasetPartCreateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        created = api_instance.create_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_create_request=dataset_part_create_request,
            file=payload["sourceName"],
        )
        if not created:
            logger.error("  [bold red]✘ API returned no data.[/bold red]")
            return CommandResponse.fail()
        logger.info(f"  [bold green]✔[/bold green] Dataset part [bold cyan]{created.id}[/bold cyan] successfully created")
        return CommandResponse.success(created.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def get_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Get dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        dataset_part = api_instance.get_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info(f"  [green]✔[/green] Dataset part [bold]{dataset_part.id}[/bold] retrieved successfully")
        return CommandResponse.success(dataset_part.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Dataset part Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def delete_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Delete dataset part by ID"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        api_instance.delete_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info(f"  [green]✔[/green] Dataset part [bold]{dataset_part_id}[/bold] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
@argument("payload_file", type=Path(exists=True))
def update_part(
    config: dict,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
    payload_file,
) -> CommandResponse:
    """Update dataset part"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_part_update_request = DatasetPartUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        updated = api_instance.update_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
            dataset_part_update_request=dataset_part_update_request,
        )
        logger.info(f"  [green]✔[/green] Dataset part [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Dataset part Failed Reason: {e}")
        return CommandResponse.fail()


@dataclass
class QueryPagination:
    offset: int = 0
    limit: int = 100
    group_bys: tuple = ()
    order_bys: tuple = ()


@dataclass
class QueryMetrics:
    selects: tuple = ()
    sums: tuple = ()
    avgs: tuple = ()
    counts: tuple = ()
    mins: tuple = ()
    maxs: tuple = ()


@datasets.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
@option(
    "--selects",
    type=str,
    multiple=True,
    help="Column names that should be part of the response data.",
)
@option(
    "--sums",
    type=str,
    multiple=True,
    help="Column names to sum by.",
)
@option(
    "--avgs",
    type=str,
    multiple=True,
    help="Column names to average by.",
)
@option(
    "--counts",
    type=str,
    multiple=True,
    help="Column names to count by.",
)
@option(
    "--mins",
    type=str,
    multiple=True,
    help="Column names to min by.",
)
@option(
    "--maxs",
    type=str,
    multiple=True,
    help="Column names to max by.",
)
@option("--offset", type=int, help="The query offset")
@option("--limit", type=int, help="The query limit")
@option("--group-bys", type=str, multiple=True, help="Column names to group by")
@option(
    "--order-bys",
    type=str,
    multiple=True,
    help="Column names to order by. Default order is ascending.",
)
def query_data(
    config: dict,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
    **kwargs,
) -> CommandResponse:
    """Query data from a dataset part"""

    metrics = QueryMetrics(
        selects=kwargs.get("selects", ()),
        sums=kwargs.get("sums", ()),
        avgs=kwargs.get("avgs", ()),
        counts=kwargs.get("counts", ()),
        mins=kwargs.get("mins", ()),
        maxs=kwargs.get("maxs", ()),
    )

    pagination = QueryPagination(
        offset=kwargs.get("offset", 0),
        limit=kwargs.get("limit", 100),
        group_bys=kwargs.get("group_bys", ()),
        order_bys=kwargs.get("order_bys", ()),
    )
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending query to API...[/dim]")
        query_result = api_instance.query_data(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
            selects=list(metrics.selects) if metrics.selects else None,
            sums=list(metrics.sums) if metrics.sums else None,
            avgs=list(metrics.avgs) if metrics.avgs else None,
            counts=list(metrics.counts) if metrics.counts else None,
            mins=list(metrics.mins) if metrics.mins else None,
            maxs=list(metrics.maxs) if metrics.maxs else None,
            offset=pagination.offset,
            limit=pagination.limit,
            group_bys=list(pagination.group_bys) if pagination.group_bys else None,
            order_bys=list(pagination.order_bys) if pagination.order_bys else None,
        )
        logger.info(f"  [green]✔[/green] Query result: {query_result}")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not query data: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def download_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Download dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        file_content = api_instance.download_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        with open(dataset_part_id, "wb") as f:
            f.write(file_content)
        logger.info(f"  [green]✔[/green] Dataset part downloaded successfully to {dataset_part_id}")
        return CommandResponse.success({"file_path": dataset_part_id})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not download dataset part: {e}")
        return CommandResponse.fail()


@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def list_parts(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """List dataset parts"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        dataset_parts = api_instance.list_dataset_parts(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
        )
        count = len(dataset_parts)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Dataset parts retrieved successfully")
        data_list = [ds.model_dump() for ds in dataset_parts]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Parts Failed Reason: {e}")
        return CommandResponse.fail()
