import asyncio
import threading
import os
from typing import Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared_types import Message, Task
from .in_memory_manager import InMemoryFakeAgentManager
from .application_manager import ApplicationManager
from .adk_host_manager import ADKHostManager
from service.types import (
    Conversation,
    Event,
    CreateConversationResponse,
    ListConversationResponse,
    SendMessageResponse,
    MessageInfo,
    ListMessageResponse,
    PendingMessageResponse,
    ListTaskResponse,
    RegisterAgentResponse,
    ListAgentResponse,
    GetEventResponse
)
import logging
logger = logging.getLogger(__name__)

# Simplified security for UI - full security implementation is in the agent framework
def sanitize_user_input(data):
    """Basic input sanitization for UI"""
    return data

def get_client_id(request):
    """Get client ID from request"""
    return request.client.host if request.client else "unknown"

class RateLimiter:
    """Simple rate limiter for demo"""
    def is_allowed(self, client_id):
        return True

class SecurityValidator:
    """Simple security validator for demo"""
    def sanitize_string(self, value, max_length=1000):
        if not value or len(value) > max_length:
            return False
        return True

class AuditLogger:
    """Simple audit logger for demo"""
    def log_security_event(self, event_type, user, data, level):
        logger.info(f"Security Event: {event_type} - {user} - {data} - {level}")

# Initialize simple security components
rate_limiter = RateLimiter()
security_validator = SecurityValidator()
audit_logger = AuditLogger()

# Security configuration
SECURITY_CONFIG = {
    "MAX_REQUEST_SIZE": 10 * 1024 * 1024,  # 10MB
    "RATE_LIMIT_WINDOW": 60,  # seconds
    "RATE_LIMIT_MAX_REQUESTS": 100,
    "ALLOWED_ORIGINS": ["http://localhost:3000", "http://localhost:12000"],
    "TRUSTED_HOSTS": ["localhost", "127.0.0.1", "::1"]
}

class ConversationServer:
  """ConversationServer is the backend to serve the agent interactions in the UI

  This defines the interface that is used by the Mesop system to interact with
  agents and provide details about the executions.
  """
  def __init__(self, router: APIRouter):
    agent_manager = os.environ.get("A2A_HOST", "ADK")
    self.manager: ApplicationManager
    if agent_manager.upper() == "ADK":
      self.manager = ADKHostManager()
    else:
      self.manager = InMemoryFakeAgentManager()

    # Note: Security middleware is handled by the main FastAPI app, not the router

    # Add API routes with security
    router.add_api_route(
        "/conversation/create",
        self._create_conversation,
        methods=["POST"])
    router.add_api_route(
        "/conversation/list",
        self._list_conversation,
        methods=["POST"])
    router.add_api_route(
        "/message/send",
        self._send_message,
        methods=["POST"])
    router.add_api_route(
        "/events/get",
        self._get_events,
        methods=["POST"])
    router.add_api_route(
        "/message/list",
        self._list_messages,
        methods=["POST"])
    router.add_api_route(
        "/message/pending",
        self._pending_messages,
        methods=["POST"])
    router.add_api_route(
        "/task/list",
        self._list_tasks,
        methods=["POST"])
    router.add_api_route(
        "/agent/register",
        self._register_agent,
        methods=["POST"])
    router.add_api_route(
        "/agent/list",
        self._list_agents,
        methods=["POST"])

  def _add_security_middleware(self, router: APIRouter):
    """Add security middleware to the router"""
    # Add CORS middleware
    router.add_middleware(
        CORSMiddleware,
        allow_origins=SECURITY_CONFIG["ALLOWED_ORIGINS"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    router.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=SECURITY_CONFIG["TRUSTED_HOSTS"]
    )

  async def _security_check(self, request: Request) -> bool:
    """Perform security checks on incoming requests"""
    client_id = get_client_id(request)
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_id):
      audit_logger.log_security_event(
          "RATE_LIMIT_EXCEEDED",
          "anonymous",
          {"client_id": client_id, "endpoint": str(request.url)},
          "WARNING"
      )
      raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    # Request size validation
    if not validate_request_size(request):
      audit_logger.log_security_event(
          "REQUEST_SIZE_EXCEEDED",
          "anonymous",
          {"client_id": client_id, "endpoint": str(request.url)},
          "WARNING"
      )
      raise HTTPException(status_code=413, detail="Request too large")
    
    return True

  def _create_conversation(self):
    """Create conversation with security logging"""
    try:
      c = self.manager.create_conversation()
      
      audit_logger.log_security_event(
          "CONVERSATION_CREATED",
          "system",
          {"conversation_id": c.id if hasattr(c, 'id') else 'unknown'},
          "INFO"
      )
      
      return CreateConversationResponse(result=c)
    except Exception as e:
      logger.error(f"Error creating conversation: {e}")
      audit_logger.log_security_event(
          "CONVERSATION_CREATION_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to create conversation")

  async def _send_message(self, request: Request):
    """Send message with security validation and sanitization"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      
      message = Message(**sanitized_message_data['params'])
      message = self.manager.sanitize_message(message)
      
      # Log message for audit
      audit_logger.log_security_event(
          "MESSAGE_SENT",
          "system",
          {
              "message_id": message.metadata.get('message_id', 'unknown'),
              "conversation_id": message.metadata.get('conversation_id', 'unknown'),
              "content_length": len(str(message.content))
          },
          "INFO"
      )
      
      t = threading.Thread(target=lambda: asyncio.run(self.manager.process_message(message)))
      t.start()
      
      return SendMessageResponse(result=MessageInfo(
          message_id=message.metadata['message_id'],
          conversation_id=message.metadata['conversation_id'] if 'conversation_id' in message.metadata else '',
      ))
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error sending message: {e}")
      audit_logger.log_security_event(
          "MESSAGE_SEND_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to send message")

  async def _list_messages(self, request: Request):
    """List messages with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      conversation_id = sanitized_message_data['params']
      
      # Validate conversation ID
      if not security_validator.sanitize_string(conversation_id, max_length=100):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
      
      conversation = self.manager.get_conversation(conversation_id)
      if conversation:
        return ListMessageResponse(result=conversation.messages)
      return ListMessageResponse(result=[])
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error listing messages: {e}")
      audit_logger.log_security_event(
          "MESSAGE_LIST_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to list messages")

  async def _pending_messages(self, request: Request):
    """Get pending messages with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      conversation_id = sanitized_message_data['params']
      
      # Validate conversation ID
      if not security_validator.sanitize_string(conversation_id, max_length=100):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
      
      pending = self.manager.get_pending_messages(conversation_id)
      
      audit_logger.log_security_event(
          "PENDING_MESSAGES_RETRIEVED",
          "system",
          {"conversation_id": conversation_id, "count": len(pending)},
          "INFO"
      )
      
      return PendingMessageResponse(result=pending)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error getting pending messages: {e}")
      audit_logger.log_security_event(
          "PENDING_MESSAGES_RETRIEVAL_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to get pending messages")

  async def _list_conversation(self, request: Request):
    """List conversations with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      conversations = self.manager.list_conversations()
      
      audit_logger.log_security_event(
          "CONVERSATIONS_LISTED",
          "system",
          {"count": len(conversations)},
          "INFO"
      )
      
      return ListConversationResponse(result=conversations)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error listing conversations: {e}")
      audit_logger.log_security_event(
          "CONVERSATIONS_LIST_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to list conversations")

  async def _get_events(self, request: Request):
    """Get events with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      conversation_id = sanitized_message_data['params']
      
      # Validate conversation ID
      if not security_validator.sanitize_string(conversation_id, max_length=100):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
      
      events = self.manager.get_events(conversation_id)
      
      audit_logger.log_security_event(
          "EVENTS_RETRIEVED",
          "system",
          {"conversation_id": conversation_id, "count": len(events)},
          "INFO"
      )
      
      return GetEventResponse(result=events)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error getting events: {e}")
      audit_logger.log_security_event(
          "EVENTS_RETRIEVAL_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to get events")

  async def _list_tasks(self, request: Request):
    """List tasks with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      conversation_id = sanitized_message_data['params']
      
      # Validate conversation ID
      if not security_validator.sanitize_string(conversation_id, max_length=100):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
      
      tasks = self.manager.get_tasks(conversation_id)
      
      audit_logger.log_security_event(
          "TASKS_RETRIEVED",
          "system",
          {"conversation_id": conversation_id, "count": len(tasks)},
          "INFO"
      )
      
      return ListTaskResponse(result=tasks)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error listing tasks: {e}")
      audit_logger.log_security_event(
          "TASKS_RETRIEVAL_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to list tasks")

  async def _register_agent(self, request: Request):
    """Register agent with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      message_data = await request.json()
      
      # Input sanitization
      sanitized_message_data = sanitize_user_input(message_data)
      agent_url = sanitized_message_data['params']
      
      # Validate agent URL
      if not security_validator.sanitize_string(agent_url, max_length=500):
        raise HTTPException(status_code=400, detail="Invalid agent URL")
      
      # Check if URL is safe (basic validation)
      if not agent_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid agent URL format")
      
      result = self.manager.register_agent(agent_url)
      
      audit_logger.log_security_event(
          "AGENT_REGISTERED",
          "system",
          {"agent_url": agent_url, "result": str(result)},
          "INFO"
      )
      
      return RegisterAgentResponse(result=result)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error registering agent: {e}")
      audit_logger.log_security_event(
          "AGENT_REGISTRATION_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to register agent")

  async def _list_agents(self, request: Request):
    """List agents with security validation"""
    try:
      # Security checks
      await self._security_check(request)
      
      agents = self.manager.list_agents()
      
      audit_logger.log_security_event(
          "AGENTS_LISTED",
          "system",
          {"count": len(agents)},
          "INFO"
      )
      
      return ListAgentResponse(result=agents)
    except HTTPException:
      raise
    except Exception as e:
      logger.error(f"Error listing agents: {e}")
      audit_logger.log_security_event(
          "AGENTS_LIST_FAILED",
          "system",
          {"error": str(e)},
          "ERROR"
      )
      raise HTTPException(status_code=500, detail="Failed to list agents")

