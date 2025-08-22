from typing import Optional, Dict, Any, List, Callable
import logging
import json
import asyncio
from datetime import datetime, timedelta
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiver
from azure.servicebus.management import ServiceBusAdministrationClient
from azure.servicebus.management import QueueProperties, TopicProperties, SubscriptionProperties
from azure.servicebus.exceptions import ServiceBusError, ServiceBusConnectionError

logger = logging.getLogger(__name__)

class AzureServiceBusClient:
    """Client for Azure Service Bus operations"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = ServiceBusClient.from_connection_string(connection_string)
        self.admin_client = ServiceBusAdministrationClient.from_connection_string(connection_string)
    
    def send_message(
        self,
        queue_or_topic_name: str,
        message_body: str,
        message_metadata: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        scheduled_enqueue_time: Optional[datetime] = None,
        is_topic: bool = False
    ) -> bool:
        """Send a message to a queue or topic"""
        try:
            if is_topic:
                # Send to topic
                with self.client.get_topic_sender(topic_name=queue_or_topic_name) as sender:
                    message = ServiceBusMessage(
                        body=message_body,
                        application_properties=message_metadata or {},
                        session_id=session_id,
                        scheduled_enqueue_time=scheduled_enqueue_time
                    )
                    sender.send_messages(message)
            else:
                # Send to queue
                with self.client.get_queue_sender(queue_name=queue_or_topic_name) as sender:
                    message = ServiceBusMessage(
                        body=message_body,
                        application_properties=message_metadata or {},
                        session_id=session_id,
                        scheduled_enqueue_time=scheduled_enqueue_time
                    )
                    sender.send_messages(message)
            
            logger.info(f"Successfully sent message to {'topic' if is_topic else 'queue'} {queue_or_topic_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {queue_or_topic_name}: {e}")
            return False
    
    def send_batch_messages(
        self,
        queue_or_topic_name: str,
        messages: List[Dict[str, Any]],
        is_topic: bool = False
    ) -> int:
        """Send multiple messages in a batch"""
        try:
            if is_topic:
                with self.client.get_topic_sender(topic_name=queue_or_topic_name) as sender:
                    service_bus_messages = []
                    for msg in messages:
                        service_bus_messages.append(ServiceBusMessage(
                            body=msg.get("body", ""),
                            application_properties=msg.get("metadata", {}),
                            session_id=msg.get("session_id"),
                            scheduled_enqueue_time=msg.get("scheduled_time")
                        ))
                    sender.send_messages(service_bus_messages)
            else:
                with self.client.get_queue_sender(queue_name=queue_or_topic_name) as sender:
                    service_bus_messages = []
                    for msg in messages:
                        service_bus_messages.append(ServiceBusMessage(
                            body=msg.get("body", ""),
                            application_properties=msg.get("metadata", {}),
                            session_id=msg.get("session_id"),
                            scheduled_enqueue_time=msg.get("scheduled_time")
                        ))
                    sender.send_messages(service_bus_messages)
            
            logger.info(f"Successfully sent {len(messages)} messages to {'topic' if is_topic else 'queue'} {queue_or_topic_name}")
            return len(messages)
            
        except Exception as e:
            logger.error(f"Error sending batch messages to {queue_or_topic_name}: {e}")
            return 0
    
    def receive_message(
        self,
        queue_or_topic_name: str,
        subscription_name: Optional[str] = None,
        max_wait_time: int = 30,
        is_topic: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Receive a single message from a queue or topic subscription"""
        try:
            if is_topic and subscription_name:
                # Receive from topic subscription
                with self.client.get_subscription_receiver(
                    topic_name=queue_or_topic_name,
                    subscription_name=subscription_name
                ) as receiver:
                    message = receiver.receive_messages(max_message_count=1, max_wait_time=max_wait_time)
                    if message:
                        msg = message[0]
                        result = {
                            "body": str(msg.body),
                            "message_id": msg.message_id,
                            "session_id": msg.session_id,
                            "metadata": dict(msg.application_properties),
                            "enqueued_time": msg.enqueued_time_utc,
                            "expires_at": msg.expires_at_utc
                        }
                        receiver.complete_message(msg)
                        return result
            else:
                # Receive from queue
                with self.client.get_queue_receiver(queue_name=queue_or_topic_name) as receiver:
                    message = receiver.receive_messages(max_message_count=1, max_wait_time=max_wait_time)
                    if message:
                        msg = message[0]
                        result = {
                            "body": str(msg.body),
                            "message_id": msg.message_id,
                            "session_id": msg.session_id,
                            "metadata": dict(msg.application_properties),
                            "enqueued_time": msg.enqueued_time_utc,
                            "expires_at": msg.expires_at_utc
                        }
                        receiver.complete_message(msg)
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message from {queue_or_topic_name}: {e}")
            return None
    
    def receive_messages(
        self,
        queue_or_topic_name: str,
        subscription_name: Optional[str] = None,
        max_messages: int = 10,
        max_wait_time: int = 30,
        is_topic: bool = False
    ) -> List[Dict[str, Any]]:
        """Receive multiple messages from a queue or topic subscription"""
        try:
            messages = []
            
            if is_topic and subscription_name:
                # Receive from topic subscription
                with self.client.get_subscription_receiver(
                    topic_name=queue_or_topic_name,
                    subscription_name=subscription_name
                ) as receiver:
                    received_messages = receiver.receive_messages(
                        max_message_count=max_messages,
                        max_wait_time=max_wait_time
                    )
                    for msg in received_messages:
                        messages.append({
                            "body": str(msg.body),
                            "message_id": msg.message_id,
                            "session_id": msg.session_id,
                            "metadata": dict(msg.application_properties),
                            "enqueued_time": msg.enqueued_time_utc,
                            "expires_at": msg.expires_at_utc
                        })
                        receiver.complete_message(msg)
            else:
                # Receive from queue
                with self.client.get_queue_receiver(queue_name=queue_or_topic_name) as receiver:
                    received_messages = receiver.receive_messages(
                        max_message_count=max_messages,
                        max_wait_time=max_wait_time
                    )
                    for msg in received_messages:
                        messages.append({
                            "body": str(msg.body),
                            "message_id": msg.message_id,
                            "session_id": msg.session_id,
                            "metadata": dict(msg.application_properties),
                            "enqueued_time": msg.enqueued_time_utc,
                            "expires_at": msg.expires_at_utc
                        })
                        receiver.complete_message(msg)
            
            logger.info(f"Received {len(messages)} messages from {'topic' if is_topic else 'queue'} {queue_or_topic_name}")
            return messages
            
        except Exception as e:
            logger.error(f"Error receiving messages from {queue_or_topic_name}: {e}")
            return []
    
    def create_queue(self, queue_name: str, properties: Optional[QueueProperties] = None) -> bool:
        """Create a new queue"""
        try:
            if not properties:
                properties = QueueProperties(queue_name)
            
            self.admin_client.create_queue(properties)
            logger.info(f"Successfully created queue {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating queue {queue_name}: {e}")
            return False
    
    def create_topic(self, topic_name: str, properties: Optional[TopicProperties] = None) -> bool:
        """Create a new topic"""
        try:
            if not properties:
                properties = TopicProperties(topic_name)
            
            self.admin_client.create_topic(properties)
            logger.info(f"Successfully created topic {topic_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating topic {topic_name}: {e}")
            return False
    
    def create_subscription(
        self,
        topic_name: str,
        subscription_name: str,
        properties: Optional[SubscriptionProperties] = None
    ) -> bool:
        """Create a new subscription for a topic"""
        try:
            if not properties:
                properties = SubscriptionProperties(subscription_name)
            
            self.admin_client.create_subscription(topic_name, properties)
            logger.info(f"Successfully created subscription {subscription_name} for topic {topic_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating subscription {subscription_name}: {e}")
            return False
    
    def delete_queue(self, queue_name: str) -> bool:
        """Delete a queue"""
        try:
            self.admin_client.delete_queue(queue_name)
            logger.info(f"Successfully deleted queue {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting queue {queue_name}: {e}")
            return False
    
    def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic"""
        try:
            self.admin_client.delete_topic(topic_name)
            logger.info(f"Successfully deleted topic {topic_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting topic {topic_name}: {e}")
            return False
    
    def get_queue_properties(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get properties of a queue"""
        try:
            properties = self.admin_client.get_queue(queue_name)
            return {
                "name": properties.name,
                "max_size_in_megabytes": properties.max_size_in_megabytes,
                "max_delivery_count": properties.max_delivery_count,
                "lock_duration": properties.lock_duration,
                "default_message_time_to_live": properties.default_message_time_to_live,
                "enable_partitioning": properties.enable_partitioning,
                "enable_session": properties.enable_session
            }
            
        except Exception as e:
            logger.error(f"Error getting queue properties for {queue_name}: {e}")
            return None
    
    def get_topic_properties(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get properties of a topic"""
        try:
            properties = self.admin_client.get_topic(topic_name)
            return {
                "name": properties.name,
                "max_size_in_megabytes": properties.max_size_in_megabytes,
                "default_message_time_to_live": properties.default_message_time_to_live,
                "enable_partitioning": properties.enable_partitioning,
                "enable_session": properties.enable_session
            }
            
        except Exception as e:
            logger.error(f"Error getting topic properties for {topic_name}: {e}")
            return None
    
    def list_queues(self) -> List[str]:
        """List all queues"""
        try:
            queues = self.admin_client.list_queues()
            return [queue.name for queue in queues]
            
        except Exception as e:
            logger.error(f"Error listing queues: {e}")
            return []
    
    def list_topics(self) -> List[str]:
        """List all topics"""
        try:
            topics = self.admin_client.list_topics()
            return [topic.name for topic in topics]
            
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return []
    
    def list_subscriptions(self, topic_name: str) -> List[str]:
        """List all subscriptions for a topic"""
        try:
            subscriptions = self.admin_client.list_subscriptions(topic_name)
            return [sub.name for sub in subscriptions]
            
        except Exception as e:
            logger.error(f"Error listing subscriptions for topic {topic_name}: {e}")
            return []
    
    def get_queue_stats(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get runtime statistics for a queue"""
        try:
            runtime_properties = self.admin_client.get_queue_runtime_properties(queue_name)
            return {
                "name": runtime_properties.name,
                "message_count": runtime_properties.message_count,
                "scheduled_message_count": runtime_properties.scheduled_message_count,
                "active_message_count": runtime_properties.active_message_count,
                "dead_letter_message_count": runtime_properties.dead_letter_message_count,
                "transfer_message_count": runtime_properties.transfer_message_count,
                "transfer_dead_letter_message_count": runtime_properties.transfer_dead_letter_message_count
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats for {queue_name}: {e}")
            return None
