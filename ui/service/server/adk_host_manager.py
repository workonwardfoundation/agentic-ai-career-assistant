import uuid
import asyncio
from typing import List, Optional, Dict, Any
from service.server.application_manager import ApplicationManager
from service.types import (
    Conversation,
    Event,
)
from shared_types import (
    Message,
    Task,
    Artifact,
    AgentCard,
    DataPart,
    FilePart,
    Part,
)
from utils.agent_card import get_agent_card
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event as ADKEvent
from google.adk.events.event_actions import EventActions as ADKEventActions
from google.genai import types
import base64


class ADKHostManager(ApplicationManager):
    """A simplified ADK host manager for the AI Career Copilot demo UI"""

    def __init__(self):
        self._conversations = []
        self._messages = []
        self._tasks = []
        self._events = {}
        self._pending_message_ids = []
        self._agents = []
        self._artifact_chunks = {}
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._memory_service = InMemoryMemoryService()
        self.user_id = "test_user"
        self.app_name = "AI-Career-Copilot"
        self._task_map = {}
        self._next_id = {}

    def create_conversation(self) -> Conversation:
        session = self._session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id
        )
        conversation_id = session.id
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def sanitize_message(self, message: Message) -> Message:
        if not message.metadata:
            message.metadata = {}
        if 'message_id' not in message.metadata:
            message.metadata.update({'message_id': str(uuid.uuid4())})
        if 'conversation_id' in message.metadata:
            conversation = self.get_conversation(message.metadata['conversation_id'])
            if conversation:
                if conversation.messages:
                    # Get the last message
                    last_message_id = self.get_message_id(conversation.messages[-1])
                    if last_message_id:
                        message.metadata.update({'last_message_id': last_message_id})
        return message

    async def process_message(self, message: Message):
        self._messages.append(message)
        message_id = self.get_message_id(message)
        if message_id:
            self._pending_message_ids.append(message_id)
        
        # Create a simple response for demo purposes
        response = Message(
            content="This is a demo response from the AI Career Copilot system. The full agent integration is being developed.",
            role="assistant",
            metadata=message.metadata.copy() if message.metadata else {}
        )
        
        # Add response to conversation
        if 'conversation_id' in message.metadata:
            conversation = self.get_conversation(message.metadata['conversation_id'])
            if conversation:
                conversation.messages.append(message)
                conversation.messages.append(response)
        
        return response

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        for conv in self._conversations:
            if conv.conversation_id == conversation_id:
                return conv
        return None

    def get_message_id(self, message: Message) -> Optional[str]:
        if message.metadata and 'message_id' in message.metadata:
            return message.metadata['message_id']
        return None

    def get_conversations(self) -> List[Conversation]:
        return self._conversations

    def get_messages(self) -> List[Message]:
        return self._messages

    def get_tasks(self) -> List[Task]:
        return self._tasks

    def get_events(self) -> List[Event]:
        return list(self._events.values())

    def get_agents(self) -> List[AgentCard]:
        return self._agents

    def add_agent(self, agent: AgentCard):
        self._agents.append(agent)

    def remove_agent(self, agent_id: str):
        self._agents = [a for a in self._agents if a.id != agent_id]

    # Required abstract methods from ApplicationManager
    @property
    def conversations(self) -> List[Conversation]:
        return self._conversations

    @property 
    def tasks(self) -> List[Task]:
        return self._tasks

    @property
    def agents(self) -> List[AgentCard]:
        return self._agents

    @property
    def events(self) -> List[Event]:
        return list(self._events.values())

    def register_agent(self, url: str):
        """Register an agent from URL"""
        try:
            agent_card = get_agent_card(url)
            self.add_agent(agent_card)
            return f"Agent registered: {agent_card.name}"
        except Exception as e:
            return f"Failed to register agent: {str(e)}"

    def get_pending_messages(self) -> List[str]:
        """Get pending message IDs"""
        return self._pending_message_ids

    # Additional methods expected by the server
    def list_conversations(self) -> List[Conversation]:
        """List all conversations"""
        return self._conversations

    def get_events(self, conversation_id: str = None) -> List[Event]:
        """Get events, optionally filtered by conversation ID"""
        if conversation_id:
            return [event for event in self._events.values() 
                   if hasattr(event, 'conversation_id') and event.conversation_id == conversation_id]
        return list(self._events.values())

    def get_tasks(self, conversation_id: str = None) -> List[Task]:
        """Get tasks, optionally filtered by conversation ID"""
        if conversation_id:
            return [task for task in self._tasks 
                   if hasattr(task, 'session_id') and task.session_id == conversation_id]
        return self._tasks

    def list_agents(self) -> List[AgentCard]:
        """List all agents"""
        return self._agents

