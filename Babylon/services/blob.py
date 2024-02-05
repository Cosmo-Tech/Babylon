from azure.storage.blob import BlobServiceClient


def blob_client(config: dict, account_secret):
    account_name = config["state"]["azure"]["storage_account_name"]
    prefix = f"DefaultEndpointsProtocol=https;AccountName={account_name}"
    connection_str = (f"{prefix};AccountKey={account_secret};EndpointSuffix=core.windows.net")
    return BlobServiceClient.from_connection_string(connection_str)
