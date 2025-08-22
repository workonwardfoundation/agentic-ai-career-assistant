from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from negotiation.task_manager import AgentTaskManager
from negotiation.agent import NegotiationAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11014)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="negotiation_coach",
      name="Negotiation Coach",
      description="Compares offers and generates counter strategies.",
      tags=["negotiation", "coach"],
      examples=["Compare these offers and suggest counters"],
    )
    agent_card = AgentCard(
      name="Negotiation Coach Agent",
      description="Offer comparison and counter strategies.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=NegotiationAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=NegotiationAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=NegotiationAgent()),
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
