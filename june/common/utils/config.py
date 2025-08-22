import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class MongoConfig:
  uri: str
  database: str

@dataclass(frozen=True)
class AzureOpenAIConfig:
  endpoint: Optional[str]
  api_key: Optional[str]
  deployment_gpt4o: Optional[str]
  deployment_gpt4o_mini: Optional[str]
  deployment_embedding_large: Optional[str]
  deployment_embedding_small: Optional[str]

@dataclass(frozen=True)
class AzureAISearchConfig:
  endpoint: Optional[str]
  api_key: Optional[str]
  index_name: Optional[str]

@dataclass(frozen=True)
class AzureBlobStorageConfig:
  connection_string: Optional[str]
  container_name: Optional[str]

@dataclass(frozen=True)
class AzureServiceBusConfig:
  connection_string: Optional[str]

@dataclass(frozen=True)
class AppConfig:
  mongo: MongoConfig
  azure_openai: AzureOpenAIConfig
  azure_ai_search: AzureAISearchConfig
  azure_blob_storage: AzureBlobStorageConfig
  azure_service_bus: AzureServiceBusConfig


def load_config() -> AppConfig:
  mongo_uri = os.getenv("MONGODB_URI", "")
  mongo_db = os.getenv("MONGODB_DB", "a2a")
  
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
  azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
  dep_gpt4o = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O")
  dep_gpt4o_mini = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
  dep_embed_large = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING_LARGE")
  dep_embed_small = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING_SMALL")

  # Azure AI Search
  azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
  azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
  azure_search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "a2a-documents")

  # Azure Blob Storage
  azure_blob_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
  azure_blob_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "a2a-artifacts")

  # Azure Service Bus
  azure_service_bus_conn_str = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")

  if not mongo_uri:
    raise ValueError("MONGODB_URI is required in environment")

  return AppConfig(
    mongo=MongoConfig(uri=mongo_uri, database=mongo_db),
    azure_openai=AzureOpenAIConfig(
      endpoint=azure_endpoint,
      api_key=azure_api_key,
      deployment_gpt4o=dep_gpt4o,
      deployment_gpt4o_mini=dep_gpt4o_mini,
      deployment_embedding_large=dep_embed_large,
      deployment_embedding_small=dep_embed_small,
    ),
    azure_ai_search=AzureAISearchConfig(
      endpoint=azure_search_endpoint,
      api_key=azure_search_api_key,
      index_name=azure_search_index,
    ),
    azure_blob_storage=AzureBlobStorageConfig(
      connection_string=azure_blob_conn_str,
      container_name=azure_blob_container,
    ),
    azure_service_bus=AzureServiceBusConfig(
      connection_string=azure_service_bus_conn_str,
    ),
  )
