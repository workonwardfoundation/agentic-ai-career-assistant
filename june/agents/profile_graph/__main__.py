from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from profile_graph.task_manager import AgentTaskManager
from profile_graph.agent import ProfileGraphAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11006)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="profile_graph",
      name="Profile Graph",
      description="Maintains canonical profile graph and serves retrieval.",
      tags=["profile", "graph"],
      examples=["Upsert this graph", "Get profile graph"],
    )
    agent_card = AgentCard(
      name="Profile Graph Agent",
      description="Canonical profile graph management and retrieval.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=ProfileGraphAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=ProfileGraphAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=ProfileGraphAgent()),
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
