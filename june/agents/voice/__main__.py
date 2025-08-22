from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from voice.task_manager import AgentTaskManager
from voice.agent import VoiceAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11016)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="voice_interaction",
      name="Voice Interaction",
      description="Real-time voice using Twilio Media Streams and Azure STT/TTS.",
      tags=["voice", "realtime"],
      examples=["Start voice session", "Process audio input"],
    )
    agent_card = AgentCard(
      name="Voice Agent",
      description="Real-time voice interactions with STT/TTS.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=VoiceAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=VoiceAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=VoiceAgent()),
      host=host,
      port=port,
    )
    server.start()
  except MissingAPIKeyError as e:
    logger.error(f"Error: {e}")
    exit(1)
  except Exception as e:
    logger.error(f"An error occurred during server startup: {e}")
    exit(1)

if __name__ == "__main__":
  main()
