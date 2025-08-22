from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from interview.task_manager import AgentTaskManager
from interview.agent import InterviewAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11013)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="interview_coach",
      name="Interview Coach",
      description="Conducts mock interviews and emits scored reports.",
      tags=["interview", "coach"],
      examples=["Start mock for Amazon SDE2"],
    )
    agent_card = AgentCard(
      name="Interview Coach Agent",
      description="Mock interviews with rubric scoring.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=InterviewAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=InterviewAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=InterviewAgent()),
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
