from logging import getLogger

from cosmotech_api.models.organization_access_control import OrganizationAccessControl
from cosmotech_api.models.organization_security import OrganizationSecurity
from cosmotech_api.models.solution_access_control import SolutionAccessControl
from cosmotech_api.models.solution_security import SolutionSecurity
from cosmotech_api.models.workspace_access_control import WorkspaceAccessControl
from cosmotech_api.models.workspace_security import WorkspaceSecurity

logger = getLogger(__name__)


def diff(
    acl1: OrganizationAccessControl | WorkspaceAccessControl | SolutionAccessControl,
    acl2: OrganizationAccessControl | WorkspaceAccessControl | SolutionAccessControl,
) -> tuple[list[str], list[str], list[str]]:
    """Generate a diff between two access control lists"""
    ids1 = [i.id for i in acl1]
    roles1 = [i.role for i in acl1]
    ids2 = [i.id for i in acl2]
    roles2 = [i.role for i in acl2]
    to_add = [item for item in ids2 if item not in ids1]
    to_delete = [item for item in ids1 if item not in ids2]
    to_update = [item for item in ids1 if item in ids2 and roles1[ids1.index(item)] != roles2[ids2.index(item)]]
    return (to_add, to_delete, to_update)


def update_default_security(
    object_type: str,
    current_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    desired_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    api_instance,
    object_id: str,
) -> None:
    if desired_security.default != current_security.default:
        try:
            getattr(api_instance, f"update_{object_type}_default_security")(
                object_id, {"role": desired_security.default}
            )
            logger.info(f"Updated {object_type} default security")
        except Exception as e:
            logger.error(f"Failed to update {object_type} default security: {e}")


def update_object_security(
    object_type: str,
    current_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    desired_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    api_instance,
    object_id: list[str],
):
    """Update object security:
    if default security differs from payload
        update object default security
    diff state vs payload
    foreach diff
      delete entries to be removed
      update entries to be changed
      create entries to be added
    """
    update_default_security(object_type, current_security, desired_security, api_instance, object_id)
    (to_add, to_delete, to_update) = diff(current_security.access_control_list, desired_security.access_control_list)
    for entry in desired_security.access_control_list:
        if entry.id in to_add:
            logger.info(f"Adding access control for id {entry.id}")
            try:
                getattr(api_instance, f"create_{object_type}_access_control")(*object_id, entry)
                logger.info(f"Access control for id {entry.id} added successfully")
            except Exception as e:
                logger.error(f"Failed to add access control for id {entry.id}: {e}")
        if entry.id in to_update:
            logger.info(f"Updating access control for id {entry.id}")
            try:
                getattr(api_instance, f"update_{object_type}_access_control")(
                    *object_id, entry.id, {"role": entry.role}
                )
                logger.info(f"Access control for id {entry.id} updated successfully")
            except Exception as e:
                logger.error(f"Failed to update access control for id {entry.id}: {e}")
    for entry_id in to_delete:
        logger.info(f"Deleting access control for id {entry_id}")
        try:
            getattr(api_instance, f"delete_{object_type}_access_control")(*object_id, entry_id)
            logger.info(f"Access control for id {entry_id} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete access control for id {entry_id}: {e}")
