from typing import List, Dict, Any, Optional
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField
)
from azure.search.documents.indexes.models import VectorSearchProfile, HnswAlgorithmConfiguration

logger = logging.getLogger(__name__)

class AzureAISearchClient:
    """Client for Azure AI Search operations including vector search"""
    
    def __init__(self, endpoint: str, api_key: str, index_name: str = "a2a-documents"):
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.credential = AzureKeyCredential(api_key)
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=self.credential
        )
    
    def create_index_if_not_exists(self) -> bool:
        """Create the search index if it doesn't exist"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.index_client.list_indexes()]
            if self.index_name in existing_indexes:
                logger.info(f"Index {self.index_name} already exists")
                return True
            
            # Define the index schema
            index = SearchIndex(
                name=self.index_name,
                fields=[
                    # Document identification
                    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                    SimpleField(name="document_type", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="agent_name", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
                    
                    # Content fields
                    SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                    SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                    SearchableField(name="summary", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                    
                    # Metadata fields
                    SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                    SimpleField(name="updated_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                    SimpleField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                    
                    # Vector search fields
                    SearchField(
                        name="content_vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        vector_search_dimensions=1536,  # OpenAI text-embedding-3-small dimensions
                        vector_search_profile_name="my-vector-config"
                    )
                ],
                vector_search_profiles=[
                    VectorSearchProfile(
                        name="my-vector-config",
                        algorithm_configuration=HnswAlgorithmConfiguration(
                            name="my-hnsw-config",
                            parameters={
                                "m": 4,
                                "efConstruction": 400,
                                "efSearch": 500,
                                "metric": "cosine"
                            }
                        )
                    )
                ]
            )
            
            # Create the index
            self.index_client.create_index(index)
            logger.info(f"Created index {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {self.index_name}: {e}")
            return False
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Index a document with vector embeddings"""
        try:
            # Ensure required fields
            if "id" not in document:
                logger.error("Document must have an 'id' field")
                return False
            
            # Index the document
            result = self.search_client.upload_documents([document])
            if result[0].succeeded:
                logger.info(f"Successfully indexed document {document['id']}")
                return True
            else:
                logger.error(f"Failed to index document {document['id']}: {result[0].errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return False
    
    def search_documents(
        self,
        query: str,
        vector_embedding: Optional[List[float]] = None,
        filters: Optional[str] = None,
        top: int = 10,
        include_total_count: bool = True
    ) -> Dict[str, Any]:
        """Search documents using text and optional vector similarity"""
        try:
            search_options = {
                "top": top,
                "include_total_count": include_total_count
            }
            
            # Add filters if provided
            if filters:
                search_options["filter"] = filters
            
            # Add vector search if embedding provided
            if vector_embedding:
                search_options["vector_queries"] = [{
                    "vector": vector_embedding,
                    "fields": "content_vector",
                    "k": top
                }]
                search_options["select"] = "id,title,content,summary,document_type,agent_name,created_at,score"
            
            # Perform the search
            results = self.search_client.search(query, **search_options)
            
            # Process results
            documents = []
            total_count = 0
            
            for result in results:
                doc = {
                    "id": result.get("id"),
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "summary": result.get("summary"),
                    "document_type": result.get("document_type"),
                    "agent_name": result.get("agent_name"),
                    "created_at": result.get("created_at"),
                    "score": result.get("@search.score", 0.0)
                }
                documents.append(doc)
            
            # Get total count if requested
            if include_total_count:
                total_count = results.get_count()
            
            return {
                "documents": documents,
                "total_count": total_count,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {
                "documents": [],
                "total_count": 0,
                "query": query,
                "error": str(e)
            }
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index"""
        try:
            result = self.search_client.delete_documents([{"id": document_id}])
            if result[0].succeeded:
                logger.info(f"Successfully deleted document {document_id}")
                return True
            else:
                logger.error(f"Failed to delete document {document_id}: {result[0].errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index_client.get_index_statistics(self.index_name)
            return {
                "document_count": stats.document_count,
                "storage_size": stats.storage_size,
                "index_size": stats.index_size
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
