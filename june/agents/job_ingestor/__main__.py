from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from job_ingestor.task_manager import AgentTaskManager
from job_ingestor.agent import JobIngestorAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11002)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="ingest_jobs",
      name="Ingest Jobs",
      description="Normalizes job postings from various sources (URLs/text).",
      tags=["ingest", "jobs"],
      examples=["Ingest jobs from these URLs: ..."],
    )
    agent_card = AgentCard(
      name="Job Ingestor Agent",
      description="Normalizes job postings.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=JobIngestorAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=JobIngestorAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=AgentTaskManager(agent=JobIngestorAgent()),
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
