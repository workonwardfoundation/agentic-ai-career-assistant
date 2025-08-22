"""
Shared type definitions for the AI Career Copilot system.
This module provides common types that are used across both the UI and agent frameworks.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskState(str, Enum):
    """Task execution states"""
    PENDING = "pending"
    WORKING = "working" 
    COMPLETED = "completed"
    FAILED = "failed"


class PartType(str, Enum):
    """Content part types"""
    TEXT = "text"
    DATA = "data"
    FILE = "file"
    IMAGE = "image"


class Part(BaseModel):
    """Base content part"""
    type: str
    
    class Config:
        extra = "allow"


class TextPart(Part):
    """Text content part"""
    type: Literal["text"] = "text"
    text: str


class DataPart(Part):
    """Data content part"""
    type: Literal["data"] = "data"
    data: Dict[str, Any]


class FilePart(Part):
    """File content part"""
    type: Literal["file"] = "file"
    file_uri: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None


class Message(BaseModel):
    """Message in a conversation"""
    role: str
    parts: List[Part] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class TaskStatus(BaseModel):
    """Status of a task"""
    state: TaskState
    message: Optional[Message] = None
    progress: Optional[float] = None
    error: Optional[str] = None


class Artifact(BaseModel):
    """Task artifact"""
    parts: List[Part] = Field(default_factory=list)
    index: int = 0
    append: bool = False
    metadata: Optional[Dict[str, Any]] = None


class Task(BaseModel):
    """Task definition"""
    id: str
    session_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    artifacts: Optional[List[Artifact]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class AgentCard(BaseModel):
    """Agent card definition"""
    name: str
    description: str
    version: Optional[str] = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    supported_content_types: List[str] = Field(default_factory=list)
    endpoint: Optional[str] = None
    
    class Config:
        extra = "allow"


# JSON-RPC Types
class JSONRPCMessage(BaseModel):
    """Base JSON-RPC message"""
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None


class JSONRPCError(BaseModel):
    """JSON-RPC error"""
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCRequest(JSONRPCMessage):
    """JSON-RPC request"""
    method: str
    params: Optional[Any] = None


class JSONRPCResponse(JSONRPCMessage):
    """JSON-RPC response"""
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# Task Management Types
class TaskSendParams(BaseModel):
    """Parameters for sending a task"""
    id: str
    sessionId: str
    message: Message
    acceptedOutputModes: List[str] = Field(default_factory=list)


class SendTaskRequest(JSONRPCRequest):
    """Request to send a task"""
    method: Literal["task/send"] = "task/send"
    params: TaskSendParams


class SendTaskResponse(JSONRPCResponse):
    """Response from sending a task"""
    result: Optional[Task] = None


class SendTaskStreamingRequest(JSONRPCRequest):
    """Request to send a streaming task"""
    method: Literal["task/send_subscribe"] = "task/send_subscribe"
    params: TaskSendParams


class TaskStatusUpdateEvent(BaseModel):
    """Task status update event"""
    id: str
    status: TaskStatus
    final: bool = False


class TaskArtifactUpdateEvent(BaseModel):
    """Task artifact update event"""
    id: str
    artifact: Artifact


class SendTaskStreamingResponse(JSONRPCResponse):
    """Response from streaming task"""
    result: Union[TaskStatusUpdateEvent, TaskArtifactUpdateEvent, None] = None


class InternalError(JSONRPCError):
    """Internal error"""
    code: int = -32603
    message: str = "Internal error"


# Conversation Types
class Conversation(BaseModel):
    """Conversation definition"""
    conversation_id: str
    is_active: bool = True
    name: str = ""
    task_ids: List[str] = Field(default_factory=list)
    messages: List[Message] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Event(BaseModel):
    """Event definition"""
    id: str
    actor: str = ""
    content: Message
    timestamp: float
    conversation_id: Optional[str] = None


# Additional UI-specific types
class AgentStatus(str, Enum):
    """Agent status"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class AgentInfo(BaseModel):
    """Extended agent information"""
    card: AgentCard
    status: AgentStatus = AgentStatus.OFFLINE
    endpoint: Optional[str] = None
    last_seen: Optional[datetime] = None
