from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from orchestrator.task_manager import AgentTaskManager as InMemAgentTaskManager
from common.server.task_manager import MongoTaskManager
from orchestrator.agent import OrchestratorAgent
import click
import os
import logging
from dotenv import load_dotenv
from common.utils.config import load_config

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=11001)
def main(host, port):
  try:
    if not os.getenv("GOOGLE_API_KEY"):
      raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
      id="plan_day",
      name="Plan Day",
      description="Creates a daily plan for job search and orchestrates downstream agents.",
      tags=["planning", "orchestration"],
      examples=["Plan my job search today"]
    )
    agent_card = AgentCard(
      name="Orchestrator Agent",
      description="Top-level planner for the career copilot.",
      url=f"http://{host}:{port}/",
      version="1.0.0",
      defaultInputModes=OrchestratorAgent.SUPPORTED_CONTENT_TYPES,
      defaultOutputModes=OrchestratorAgent.SUPPORTED_CONTENT_TYPES,
      capabilities=capabilities,
      skills=[skill],
    )

    # Prefer Mongo if configured
    task_manager = None
    try:
      cfg = load_config()
      task_manager = MongoTaskManager(mongo_uri=cfg.mongo.uri, database=cfg.mongo.database)
    except Exception as e:
      logger.info(f"Mongo not configured or unavailable, using in-memory task manager: {e}")
      task_manager = InMemAgentTaskManager(agent=OrchestratorAgent())

    # If Mongo is used, still need the AgentTaskManager semantics; wrap by composition
    if isinstance(task_manager, MongoTaskManager):
      from common.server.task_manager import InMemoryTaskManager as BaseTM
      base_tm = InMemAgentTaskManager(agent=OrchestratorAgent())
      # Monkey patch MongoTaskManager with AgentTaskManager methods
      task_manager.__class__ = type(
        "MongoOrchestratorTaskManager",
        (MongoTaskManager, BaseTM.__class__),
        dict(base_tm.__class__.__dict__)
      )

    server = A2AServer(
      agent_card=agent_card,
      task_manager=task_manager if not isinstance(task_manager, MongoTaskManager) else base_tm,
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
