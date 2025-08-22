from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from prompt_library.task_manager import AgentTaskManager
from prompt_library.agent import PromptLibraryAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11015)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="prompt_management",
      name="Prompt Management",
      description="Centralized prompt versioning and AB testing.",
      tags=["prompt", "library"],
      examples=["Create new prompt version", "Get AB test prompts"],
    )
    agent_card = AgentCard(
      name="Prompt Library Agent",
      description="Centralized prompt management with versioning and AB testing.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=PromptLibraryAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=PromptLibraryAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=PromptLibraryAgent()),
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
