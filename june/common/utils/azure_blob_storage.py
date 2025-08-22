from typing import Optional, List, Dict, Any, BinaryIO
import logging
import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

logger = logging.getLogger(__name__)

class AzureBlobStorageClient:
    """Client for Azure Blob Storage operations"""
    
    def __init__(self, connection_string: str, container_name: str = "a2a-artifacts"):
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        
        # Ensure container exists
        self._ensure_container_exists()
    
    def _ensure_container_exists(self) -> bool:
        """Create the container if it doesn't exist"""
        try:
            self.container_client.get_container_properties()
            logger.info(f"Container {self.container_name} already exists")
            return True
        except ResourceNotFoundError:
            try:
                self.blob_service_client.create_container(self.container_name)
                logger.info(f"Created container {self.container_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to create container {self.container_name}: {e}")
                return False
    
    def upload_file(
        self,
        file_path: str,
        blob_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """Upload a file to blob storage"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} does not exist")
                return None
            
            # Use provided blob name or generate from file path
            if not blob_name:
                blob_name = os.path.basename(file_path)
            
            # Get blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Upload the file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    metadata=metadata,
                    content_type=content_type
                )
            
            logger.info(f"Successfully uploaded {file_path} to {blob_name}")
            return blob_name
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return None
    
    def upload_data(
        self,
        data: bytes,
        blob_name: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """Upload data bytes to blob storage"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            blob_client.upload_blob(
                data,
                overwrite=True,
                metadata=metadata,
                content_type=content_type
            )
            
            logger.info(f"Successfully uploaded data to {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading data to {blob_name}: {e}")
            return False
    
    def download_file(self, blob_name: str, destination_path: str) -> bool:
        """Download a blob to a local file"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Download the blob
            with open(destination_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"Successfully downloaded {blob_name} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {blob_name}: {e}")
            return False
    
    def download_data(self, blob_name: str) -> Optional[bytes]:
        """Download a blob as bytes"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
            
        except Exception as e:
            logger.error(f"Error downloading {blob_name}: {e}")
            return None
    
    def delete_blob(self, blob_name: str) -> bool:
        """Delete a blob from storage"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Successfully deleted {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {blob_name}: {e}")
            return False
    
    def list_blobs(
        self,
        name_starts_with: Optional[str] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """List blobs in the container"""
        try:
            blobs = []
            
            # List blobs with optional prefix
            if name_starts_with:
                blob_list = self.container_client.list_blobs(name_starts_with=name_starts_with)
            else:
                blob_list = self.container_client.list_blobs()
            
            for blob in blob_list:
                blob_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "created": blob.creation_time,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type,
                    "etag": blob.etag
                }
                
                if include_metadata and blob.metadata:
                    blob_info["metadata"] = blob.metadata
                
                blobs.append(blob_info)
            
            return blobs
            
        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            return []
    
    def get_blob_properties(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """Get properties of a specific blob"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            
            return {
                "name": properties.name,
                "size": properties.size,
                "created": properties.creation_time,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "etag": properties.etag,
                "metadata": properties.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting properties for {blob_name}: {e}")
            return None
    
    def generate_sas_url(
        self,
        blob_name: str,
        permission: str = "r",
        expiry_hours: int = 24
    ) -> Optional[str]:
        """Generate a SAS URL for a blob"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Set permissions
            permissions = BlobSasPermissions()
            if "r" in permission:
                permissions.read = True
            if "w" in permission:
                permissions.write = True
            if "d" in permission:
                permissions.delete = True
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=blob_client.container_name,
                blob_name=blob_client.blob_name,
                account_key=blob_client.credential.account_key,
                permission=permissions,
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Return full URL
            return f"{blob_client.url}?{sas_token}"
            
        except Exception as e:
            logger.error(f"Error generating SAS URL for {blob_name}: {e}")
            return None
    
    def copy_blob(
        self,
        source_blob_name: str,
        destination_blob_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Copy a blob within the same container"""
        try:
            source_blob = self.container_client.get_blob_client(source_blob_name)
            destination_blob = self.container_client.get_blob_client(destination_blob_name)
            
            # Start copy operation
            destination_blob.start_copy_from_url(source_blob.url)
            
            # Update metadata if provided
            if metadata:
                destination_blob.set_blob_metadata(metadata)
            
            logger.info(f"Successfully copied {source_blob_name} to {destination_blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying blob {source_blob_name}: {e}")
            return False
    
    def get_container_stats(self) -> Dict[str, Any]:
        """Get container statistics"""
        try:
            # List all blobs to calculate stats
            blobs = list(self.container_client.list_blobs())
            
            total_size = sum(blob.size for blob in blobs)
            total_count = len(blobs)
            
            # Group by content type
            content_types = {}
            for blob in blobs:
                content_type = blob.content_settings.content_type or "unknown"
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            return {
                "container_name": self.container_name,
                "total_blobs": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "content_types": content_types
            }
            
        except Exception as e:
            logger.error(f"Error getting container stats: {e}")
            return {}
