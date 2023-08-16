def SUCCESS_PAYLOAD_CREATED(resource):
    return f"Successfully created: {resource} payload"


def SUCCESS_CREATED(resource, id):
    return f"Successfully created: {resource} with id: {id}"


def SUCCESS__RBAC_UPDATED(resource):
    return f"Successfully updated: {resource} RBAC"


def SUCCESS_UPDATED(resource, id):
    return f"Successfully updated: {resource} with id: {id}"


def SUCCESS_DELETED(resource, id):
    return f"Successfully deleted: {resource} with id: {id}"


def SUCCESS_CONFIG_UPDATED(resource, key):
    return f"Successfully updated: variable {key} in {resource}"
