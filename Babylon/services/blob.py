from azure.storage.blob import BlobServiceClient


def blob_client(storage_name: str, account_secret):
    prefix = f"DefaultEndpointsProtocol=https;AccountName={storage_name}"
    connection_str = (f"{prefix};AccountKey={account_secret};EndpointSuffix=core.windows.net")
    return BlobServiceClient.from_connection_string(connection_str)
