from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from onboarding.task_manager import AgentTaskManager
from onboarding.agent import OnboardingAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11005)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="build_profile_graph",
      name="Build Profile Graph",
      description="Parses resume/profile to build a Profile Graph JSON.",
      tags=["onboarding", "profile"],
      examples=["Parse this resume and build my profile graph"],
    )
    agent_card = AgentCard(
      name="Onboarding Agent",
      description="Parses resumes/LinkedIn profile text and emits a Profile Graph.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=OnboardingAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=OnboardingAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=OnboardingAgent()),
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
