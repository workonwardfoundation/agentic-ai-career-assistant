from typing import Any, AsyncIterable, Dict
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
import json

class ComplianceAgent:
  SUPPORTED_CONTENT_TYPES = ["text", "application/json"]

  def __init__(self):
    self._agent = self._build_agent()
    self._runner = Runner(
      app_name=self._agent.name,
      agent=self._agent,
      artifact_service=InMemoryArtifactService(),
      session_service=InMemorySessionService(),
      memory_service=InMemoryMemoryService(),
    )
    self._user_id = "compliance"

  def _build_agent(self) -> LlmAgent:
    return LlmAgent(
      model="gemini-2.0-flash-001",
      name="compliance",
      description="Performs ToS checks, PII redaction, and content safety on artifacts.",
      instruction=(
        "Input: JSON {artifact, context}. Output: JSON {pass: bool, reasons[], redactions[], signed_at}"
      ),
      tools=[],
    )

  def invoke(self, query: str, session_id: str) -> str:
    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
    events = self._runner.run(user_id=self._user_id, session_id=session_id, new_message=content)
    if not events or not events[-1].content or not events[-1].content.parts:
      return json.dumps({})
    text = "\n".join([p.text for p in events[-1].content.parts if p.text])
    try:
      json.loads(text)
      return text
    except:
      return json.dumps({})

  async def stream(self, query: str, session_id: str):
    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
    async for event in self._runner.run_async(user_id=self._user_id, session_id=session_id, new_message=content):
      if event.is_final_response():
        response = "\n".join([p.text for p in event.content.parts if p.text]) if event.content and event.content.parts else "{}"
        yield {"is_task_complete": True, "content": response}
      else:
        yield {"is_task_complete": False, "updates": "Running safety checks..."}
