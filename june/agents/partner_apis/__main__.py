from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from partner_apis.task_manager import AgentTaskManager
from partner_apis.agent import PartnerAPIAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11017)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="partner_integration",
      name="Partner Integration",
      description="Integrates with LinkedIn, Indeed, and other job platforms.",
      tags=["partner", "api"],
      examples=["Search LinkedIn jobs", "Check Indeed status"],
    )
    agent_card = AgentCard(
      name="Partner APIs Agent",
      description="Integration with external job platforms and APIs.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=PartnerAPIAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=PartnerAPIAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=PartnerAPIAgent()),
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
