from typing import Optional, Dict, Any
import logging
from .config import AppConfig
from .azure_ai_search import AzureAISearchClient
from .azure_blob_storage import AzureBlobStorageClient
from .azure_service_bus import AzureServiceBusClient
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureServicesManager:
    """Unified manager for all Azure services"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._ai_search_client: Optional[AzureAISearchClient] = None
        self._blob_storage_client: Optional[AzureBlobStorageClient] = None
        self._service_bus_client: Optional[AzureServiceBusClient] = None
    
    @property
    def ai_search(self) -> Optional[AzureAISearchClient]:
        """Get Azure AI Search client"""
        if not self._ai_search_client and self.config.azure_ai_search.endpoint and self.config.azure_ai_search.api_key:
            try:
                self._ai_search_client = AzureAISearchClient(
                    endpoint=self.config.azure_ai_search.endpoint,
                    api_key=self.config.azure_ai_search.api_key,
                    index_name=self.config.azure_ai_search.index_name or "a2a-documents"
                )
                # Ensure index exists
                self._ai_search_client.create_index_if_not_exists()
                logger.info("Azure AI Search client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure AI Search client: {e}")
                self._ai_search_client = None
        
        return self._ai_search_client
    
    @property
    def blob_storage(self) -> Optional[AzureBlobStorageClient]:
        """Get Azure Blob Storage client"""
        if not self._blob_storage_client and self.config.azure_blob_storage.connection_string:
            try:
                self._blob_storage_client = AzureBlobStorageClient(
                    connection_string=self.config.azure_blob_storage.connection_string,
                    container_name=self.config.azure_blob_storage.container_name or "a2a-artifacts"
                )
                logger.info("Azure Blob Storage client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
                self._blob_storage_client = None
        
        return self._blob_storage_client
    
    @property
    def service_bus(self) -> Optional[AzureServiceBusClient]:
        """Get Azure Service Bus client"""
        if not self._service_bus_client and self.config.azure_service_bus.connection_string:
            try:
                self._service_bus_client = AzureServiceBusClient(
                    connection_string=self.config.azure_service_bus.connection_string
                )
                logger.info("Azure Service Bus client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Service Bus client: {e}")
                self._service_bus_client = None
        
        return self._service_bus_client
    
    def is_ai_search_available(self) -> bool:
        """Check if Azure AI Search is available"""
        return self.ai_search is not None
    
    def is_blob_storage_available(self) -> bool:
        """Check if Azure Blob Storage is available"""
        return self.blob_storage is not None
    
    def is_service_bus_available(self) -> bool:
        """Check if Azure Service Bus is available"""
        return self.service_bus is not None
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all Azure services"""
        return {
            "ai_search": self.is_ai_search_available(),
            "blob_storage": self.is_blob_storage_available(),
            "service_bus": self.is_service_bus_available()
        }
    
    def initialize_services(self) -> Dict[str, bool]:
        """Initialize all available Azure services"""
        status = {}
        
        # Initialize AI Search
        if self.config.azure_ai_search.endpoint and self.config.azure_ai_search.api_key:
            try:
                _ = self.ai_search
                status["ai_search"] = True
            except Exception as e:
                logger.error(f"Failed to initialize AI Search: {e}")
                status["ai_search"] = False
        
        # Initialize Blob Storage
        if self.config.azure_blob_storage.connection_string:
            try:
                _ = self.blob_storage
                status["blob_storage"] = True
            except Exception as e:
                logger.error(f"Failed to initialize Blob Storage: {e}")
                status["blob_storage"] = False
        
        # Initialize Service Bus
        if self.config.azure_service_bus.connection_string:
            try:
                _ = self.service_bus
                status["service_bus"] = True
            except Exception as e:
                logger.error(f"Failed to initialize Service Bus: {e}")
                status["service_bus"] = False
        
        return status
    
    def create_default_queues_and_topics(self) -> Dict[str, bool]:
        """Create default Service Bus queues and topics for the system"""
        if not self.service_bus:
            logger.warning("Service Bus not available, skipping queue/topic creation")
            return {}
        
        results = {}
        
        # Create default queues
        default_queues = [
            "job-ingestion",
            "matching",
            "application-processing",
            "notification"
        ]
        
        for queue_name in default_queues:
            try:
                success = self.service_bus.create_queue(queue_name)
                results[f"queue_{queue_name}"] = success
                if success:
                    logger.info(f"Created default queue: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to create queue {queue_name}: {e}")
                results[f"queue_{queue_name}"] = False
        
        # Create default topics
        default_topics = [
            "user-events",
            "system-events",
            "compliance-events"
        ]
        
        for topic_name in default_topics:
            try:
                success = self.service_bus.create_topic(topic_name)
                results[f"topic_{topic_name}"] = success
                if success:
                    # Create default subscription
                    sub_success = self.service_bus.create_subscription(topic_name, "default")
                    results[f"subscription_{topic_name}_default"] = sub_success
                    logger.info(f"Created default topic: {topic_name}")
            except Exception as e:
                logger.error(f"Failed to create topic {topic_name}: {e}")
                results[f"topic_{topic_name}"] = False
        
        return results
    
    def send_system_event(self, event_type: str, event_data: Dict[str, Any], priority: str = "normal") -> bool:
        """Send a system event to the Service Bus"""
        if not self.service_bus:
            logger.warning("Service Bus not available, cannot send system event")
            return False
        
        try:
            message_body = {
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": str(datetime.utcnow()),
                "priority": priority
            }
            
            success = self.service_bus.send_message(
                queue_or_topic_name="system-events",
                message_body=str(message_body),
                message_metadata={
                    "event_type": event_type,
                    "priority": priority,
                    "source": "a2a-career-copilot"
                },
                is_topic=True
            )
            
            if success:
                logger.info(f"Sent system event: {event_type}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send system event {event_type}: {e}")
            return False
    
    def store_artifact(self, artifact_data: bytes, artifact_name: str, metadata: Dict[str, str]) -> Optional[str]:
        """Store an artifact in Blob Storage"""
        if not self.blob_storage:
            logger.warning("Blob Storage not available, cannot store artifact")
            return None
        
        try:
            success = self.blob_storage.upload_data(
                data=artifact_data,
                blob_name=artifact_name,
                metadata=metadata,
                content_type="application/octet-stream"
            )
            
            if success:
                logger.info(f"Stored artifact: {artifact_name}")
                return artifact_name
            return None
            
        except Exception as e:
            logger.error(f"Failed to store artifact {artifact_name}: {e}")
            return None
    
    def search_documents(self, query: str, filters: Optional[str] = None, top: int = 10) -> Dict[str, Any]:
        """Search documents using Azure AI Search"""
        if not self.ai_search:
            logger.warning("AI Search not available, returning empty results")
            return {
                "documents": [],
                "total_count": 0,
                "query": query,
                "error": "AI Search not available"
            }
        
        try:
            return self.ai_search.search_documents(
                query=query,
                filters=filters,
                top=top
            )
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return {
                "documents": [],
                "total_count": 0,
                "query": query,
                "error": str(e)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health including Azure services"""
        health = {
            "timestamp": str(datetime.utcnow()),
            "azure_services": self.get_service_status(),
            "overall_status": "healthy"
        }
        
        # Check each service
        service_status = self.get_service_status()
        if not any(service_status.values()):
            health["overall_status"] = "unavailable"
        elif not all(service_status.values()):
            health["overall_status"] = "degraded"
        
        # Add service-specific health checks
        if self.ai_search:
            try:
                stats = self.ai_search.get_index_stats()
                health["ai_search_stats"] = stats
            except Exception as e:
                health["ai_search_stats"] = {"error": str(e)}
        
        if self.blob_storage:
            try:
                stats = self.blob_storage.get_container_stats()
                health["blob_storage_stats"] = stats
            except Exception as e:
                health["blob_storage_stats"] = {"error": str(e)}
        
        if self.service_bus:
            try:
                queues = self.service_bus.list_queues()
                topics = self.service_bus.list_topics()
                health["service_bus_stats"] = {
                    "queues": len(queues),
                    "topics": len(topics)
                }
            except Exception as e:
                health["service_bus_stats"] = {"error": str(e)}
        
        return health
