import logging

from pprint import pformat
from typing import Iterable
from uuid import uuid4
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from azure.mgmt.kusto.models import DatabasePrincipalAssignment

logger = logging.getLogger("Babylon")


class AdxPermissionService:

    def __init__(self, kusto_client: KustoManagementClient, state: dict = None) -> None:
        self.state = state
        self.kusto_client = kusto_client

    def set(self, principal_id: str, principal_type: str, role: str, tenant_id: str):
        if role not in ["User", "Viewer", "Admin"]:
            logger.error('Only values accepted: "User", "Viewer", "Admin"')
            return False
        if principal_type not in ["User", "Group", "App"]:
            logger.error('Only values accepted: "User", "Group", "App"')
            return False
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        parameters = DatabasePrincipalAssignment(
            principal_id=principal_id,
            principal_type=principal_type,
            role=role,
            tenant_id=tenant_id,
        )
        principal_assignment_name = str(uuid4())
        logger.info("Creating assignment...")
        try:
            poller = (self.kusto_client.database_principal_assignments.begin_create_or_update(
                principal_assignment_name=principal_assignment_name,
                cluster_name=adx_cluster_name,
                resource_group_name=resource_group_name,
                database_name=database_name,
                parameters=parameters,
            ))
            if poller.done():
                logger.info("Successfully created")
        except Exception as exp:
            logger.warning(exp)
            return None

    def delete(
        self,
        principal_id: str,
        force_validation: bool,
    ):
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        assignments = self.kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                            database_name)
        entity_assignments = [assign for assign in assignments if assign.principal_id == principal_id]
        if not entity_assignments:
            logger.error(f"No assignment found for principal ID {principal_id}")
            return CommandResponse.fail()

        logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
        for assign in entity_assignments:
            if not force_validation and not confirm_deletion("permission", str(assign.role)):
                return CommandResponse.fail()

            logger.info(f"Deleting role {assign.role} to principal {assign.principal_type}: {assign.principal_id}")
            assign_name: str = str(assign.name).split("/")[-1]
            poller = self.kusto_client.database_principal_assignments.begin_delete(
                resource_group_name,
                adx_cluster_name,
                database_name,
                principal_assignment_name=assign_name,
            )
            poller.wait()
            # check if done
            if not poller.done():
                return False
            return True

    def get(self, principal_id: str):
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        try:
            assignments = self.kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                                database_name)
            entity_assignments = [assignment for assignment in assignments if assignment.principal_id == principal_id]
            if not entity_assignments:
                logger.info(f"No assignment found for principal ID {principal_id}")
                return False
            logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
            for ent in entity_assignments:
                logger.info(f"{pformat(ent.__dict__)}")
            return entity_assignments
        except Exception as exp:
            logger.warning(exp)
            return None

    def get_all(self) -> Iterable[DatabasePrincipalAssignment]:
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        result = list()
        try:
            assignments = self.kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                                database_name)

            for ent in assignments:
                result.append(ent.__dict__)
            return result
        except Exception as exp:
            logger.warning(exp)
            return result
