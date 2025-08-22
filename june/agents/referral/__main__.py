from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from referral.task_manager import AgentTaskManager
from referral.agent import ReferralAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11010)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="plan_referrals",
      name="Plan Referrals",
      description="Finds insiders and drafts outreach variants.",
      tags=["referral", "planner"],
      examples=["Find alumni at X and draft messages"],
    )
    agent_card = AgentCard(
      name="Referral Planner Agent",
      description="Targets insiders and drafts outreach.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=ReferralAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=ReferralAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=ReferralAgent()),
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
