from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from multilingual.task_manager import AgentTaskManager
from multilingual.agent import MultilingualAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11018)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="multilingual_support",
      name="Multilingual Support",
      description="Translation, localization, and multilingual support.",
      tags=["multilingual", "translation"],
      examples=["Translate to Spanish", "Localize for German market"],
    )
    agent_card = AgentCard(
      name="Multilingual Agent",
      description="Handles translation and localization for global users.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=MultilingualAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=MultilingualAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=MultilingualAgent()),
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
