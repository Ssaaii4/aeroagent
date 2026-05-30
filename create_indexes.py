from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
load_dotenv()

SEARCH_ENDPOINT  = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_ADMIN_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]

ic = SearchIndexClient(SEARCH_ENDPOINT, AzureKeyCredential(SEARCH_ADMIN_KEY))

def create_indexes():
    ic.create_or_update_index(SearchIndex(
        name="flight-cache",
        fields=[
            SearchField(name="id",           type=SearchFieldDataType.String, key=True,  filterable=True),
            SearchField(name="cache_key",    type=SearchFieldDataType.String,            filterable=True),
            SearchField(name="origin",       type=SearchFieldDataType.String,            filterable=True),
            SearchField(name="destination",  type=SearchFieldDataType.String,            filterable=True),
            SearchField(name="date",         type=SearchFieldDataType.String,            filterable=True),
            SearchField(name="time_pref",    type=SearchFieldDataType.String,            filterable=True),
            SearchField(name="flights_json", type=SearchFieldDataType.String,            filterable=False),
            SearchField(name="cached_at",    type=SearchFieldDataType.String,            filterable=True),
        ]
    ))
    print("flight-cache index created")

    ic.create_or_update_index(SearchIndex(
        name="approvals",
        fields=[
            SearchField(name="id",           type=SearchFieldDataType.String, key=True, filterable=True),
            SearchField(name="status",       type=SearchFieldDataType.String,           filterable=True),
            SearchField(name="triggered_at", type=SearchFieldDataType.String,           filterable=True),
            SearchField(name="approved_at",  type=SearchFieldDataType.String,           filterable=True),
        ]
    ))
    print("approvals index created")

if __name__ == "__main__":
    create_indexes()