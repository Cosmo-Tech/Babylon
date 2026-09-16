def success_payload_created(resource):
    return f"Successfully created: {resource} payload"


def success_created(resource, id):
    return f"Successfully created: {resource} with id: {id}"


def success_rbac_updated(resource):
    return f"Successfully updated: {resource} RBAC"


def success_updated(resource, id):
    return f"Successfully updated: {resource} with id: {id}"


def success_deleted(resource, id):
    return f"Successfully deleted: {resource} with id: {id}"


def success_config_updated(resource, key):
    return f"Successfully updated: variable {key} in {resource}"
