from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from config import KV_URL

_client = None

def get_secret(name: str) -> str:
    global _client
    if not _client:
        _client = SecretClient(
            vault_url=KV_URL,
            credential=DefaultAzureCredential()
        )
    return _client.get_secret(name).value