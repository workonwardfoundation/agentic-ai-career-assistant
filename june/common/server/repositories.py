from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from common.utils.config import load_config
from common.utils.security import (
    security_validator,
    audit_logger,
    sanitize_user_input
)
import logging
import re

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db = None

async def get_db():
  global _client, _db
  if _db is not None:
    return _db
  cfg = load_config()
  _client = AsyncIOMotorClient(cfg.mongo.uri)
  _db = _client[cfg.mongo.database]
  return _db

def _validate_and_sanitize_input(data: Any, operation: str) -> Any:
    """Validate and sanitize input data before database operations"""
    try:
        # Sanitize the input
        sanitized_data = sanitize_user_input(data)
        
        # Log the operation for audit
        audit_logger.log_security_event(
            "DB_OPERATION",
            "system",
            {
                "operation": operation,
                "data_type": type(data).__name__,
                "sanitized": True
            },
            "INFO"
        )
        
        return sanitized_data
    except Exception as e:
        logger.error(f"Input validation failed for {operation}: {e}")
        audit_logger.log_security_event(
            "INPUT_VALIDATION_FAILED",
            "system",
            {
                "operation": operation,
                "error": str(e),
                "data": str(data)[:100]  # Truncate for logging
            },
            "ERROR"
        )
        raise ValueError(f"Input validation failed: {e}")

def _validate_user_id(user_id: str) -> str:
    """Validate user ID format and sanitize"""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("User ID must be a non-empty string")
    
    # Sanitize user ID
    sanitized_id = security_validator.sanitize_string(user_id, max_length=100)
    
    # Validate format (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z0-9_]+$', sanitized_id):
        raise ValueError("User ID contains invalid characters")
    
    return sanitized_id

async def save_jobs(jobs: List[Dict[str, Any]]) -> int:
  """Save jobs with input validation and sanitization"""
  try:
    db = await get_db()
    if not jobs:
      return 0
    
    # Validate and sanitize each job
    sanitized_jobs = []
    for job in jobs:
      sanitized_job = _validate_and_sanitize_input(job, "save_jobs")
      sanitized_job.setdefault("_type", "job")
      sanitized_jobs.append(sanitized_job)
    
    res = await db["jobs"].insert_many(sanitized_jobs)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "jobs", "count": len(res.inserted_ids)},
        "INFO"
    )
    
    return len(res.inserted_ids)
  except Exception as e:
    logger.error(f"Error saving jobs: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "jobs", "error": str(e)},
        "ERROR"
    )
    raise

async def save_matches(matches: List[Dict[str, Any]]) -> int:
  """Save matches with input validation and sanitization"""
  try:
    db = await get_db()
    if not matches:
      return 0
    
    # Validate and sanitize each match
    sanitized_matches = []
    for match in matches:
      sanitized_match = _validate_and_sanitize_input(match, "save_matches")
      sanitized_match.setdefault("_type", "match")
      sanitized_matches.append(sanitized_match)
    
    res = await db["matches"].insert_many(sanitized_matches)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "matches", "count": len(res.inserted_ids)},
        "INFO"
    )
    
    return len(res.inserted_ids)
  except Exception as e:
    logger.error(f"Error saving matches: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "matches", "error": str(e)},
        "ERROR"
    )
    raise

async def save_tailor_result(result: Dict[str, Any]) -> str:
  """Save tailor result with input validation and sanitization"""
  try:
    db = await get_db()
    if not result:
      return ""
    
    sanitized_result = _validate_and_sanitize_input(result, "save_tailor_result")
    sanitized_result.setdefault("_type", "tailor_result")
    
    res = await db["tailor_results"].insert_one(sanitized_result)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "tailor_results", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving tailor result: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "tailor_results", "error": str(e)},
        "ERROR"
    )
    raise

async def save_profile(user_id: str, profile: Dict[str, Any]) -> str:
  """Save profile with input validation and sanitization"""
  try:
    # Validate user ID
    validated_user_id = _validate_user_id(user_id)
    
    # Validate and sanitize profile data
    sanitized_profile = _validate_and_sanitize_input(profile, "save_profile")
    
    db = await get_db()
    profile_doc = {"_type": "profile", "user_id": validated_user_id, **sanitized_profile}
    
    res = await db["profiles"].update_one(
      {"user_id": validated_user_id}, 
      {"$set": profile_doc}, 
      upsert=True
    )
    
    audit_logger.log_security_event(
        "DB_UPDATE_SUCCESS",
        "system",
        {"collection": "profiles", "user_id": validated_user_id},
        "INFO"
    )
    
    return validated_user_id
  except Exception as e:
    logger.error(f"Error saving profile: {e}")
    audit_logger.log_security_event(
        "DB_UPDATE_FAILED",
        "system",
        {"collection": "profiles", "user_id": user_id, "error": str(e)},
        "ERROR"
    )
    raise

async def save_profile_graph(user_id: str, graph: Dict[str, Any]) -> str:
  """Save profile graph with input validation and sanitization"""
  try:
    # Validate user ID
    validated_user_id = _validate_user_id(user_id)
    
    # Validate and sanitize graph data
    sanitized_graph = _validate_and_sanitize_input(graph, "save_profile_graph")
    
    db = await get_db()
    graph_doc = {"_type": "profile_graph", "user_id": validated_user_id, **sanitized_graph}
    
    res = await db["profile_graphs"].update_one(
      {"user_id": validated_user_id}, 
      {"$set": graph_doc}, 
      upsert=True
    )
    
    audit_logger.log_security_event(
        "DB_UPDATE_SUCCESS",
        "system",
        {"collection": "profile_graphs", "user_id": validated_user_id},
        "INFO"
    )
    
    return validated_user_id
  except Exception as e:
    logger.error(f"Error saving profile graph: {e}")
    audit_logger.log_security_event(
        "DB_UPDATE_FAILED",
        "system",
        {"collection": "profile_graphs", "user_id": user_id, "error": str(e)},
        "ERROR"
    )
    raise

async def save_application(app: Dict[str, Any]) -> str:
  """Save application with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_app = _validate_and_sanitize_input(app, "save_application")
    sanitized_app.setdefault("_type", "application")
    
    res = await db["applications"].insert_one(sanitized_app)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "applications", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving application: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "applications", "error": str(e)},
        "ERROR"
    )
    raise

async def save_referrals(referrals: List[Dict[str, Any]]) -> int:
  """Save referrals with input validation and sanitization"""
  try:
    db = await get_db()
    if not referrals:
      return 0
    
    # Validate and sanitize each referral
    sanitized_referrals = []
    for referral in referrals:
      sanitized_referral = _validate_and_sanitize_input(referral, "save_referrals")
      sanitized_referral.setdefault("_type", "referral")
      sanitized_referrals.append(sanitized_referral)
    
    res = await db["referrals"].insert_many(sanitized_referrals)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "referrals", "count": len(res.inserted_ids)},
        "INFO"
    )
    
    return len(res.inserted_ids)
  except Exception as e:
    logger.error(f"Error saving referrals: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "referrals", "error": str(e)},
        "ERROR"
    )
    raise

async def save_outreach_message(msg: Dict[str, Any]) -> str:
  """Save outreach message with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_msg = _validate_and_sanitize_input(msg, "save_outreach_message")
    sanitized_msg.setdefault("_type", "outreach_message")
    
    res = await db["outreach_messages"].insert_one(sanitized_msg)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "outreach_messages", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving outreach message: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "outreach_messages", "error": str(e)},
        "ERROR"
    )
    raise

async def save_event(event: Dict[str, Any]) -> str:
  """Save event with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_event = _validate_and_sanitize_input(event, "save_event")
    sanitized_event.setdefault("_type", "event")
    
    res = await db["audit_logs"].insert_one(sanitized_event)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "audit_logs", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving event: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "audit_logs", "error": str(e)},
        "ERROR"
    )
    raise

async def save_compliance_artifact(artifact: Dict[str, Any]) -> str:
  """Save compliance artifact with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_artifact = _validate_and_sanitize_input(artifact, "save_compliance_artifact")
    sanitized_artifact.setdefault("_type", "compliance_artifact")
    
    res = await db["compliance_artifacts"].insert_one(sanitized_artifact)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "compliance_artifacts", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving compliance artifact: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "compliance_artifacts", "error": str(e)},
        "ERROR"
    )
    raise

async def save_interview_report(report: Dict[str, Any]) -> str:
  """Save interview report with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_report = _validate_and_sanitize_input(report, "save_interview_report")
    sanitized_report.setdefault("_type", "interview_report")
    
    res = await db["interview_reports"].insert_one(sanitized_report)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "interview_reports", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving interview report: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "interview_reports", "error": str(e)},
        "ERROR"
    )
    raise

async def save_offer_comparison(comp: Dict[str, Any]) -> str:
  """Save offer comparison with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_comp = _validate_and_sanitize_input(comp, "save_offer_comparison")
    sanitized_comp.setdefault("_type", "offer_comparison")
    
    res = await db["offer_comparisons"].insert_one(sanitized_comp)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "offer_comparisons", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving offer comparison: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "offer_comparisons", "error": str(e)},
        "ERROR"
    )
    raise

async def save_prompt_version(prompt: Dict[str, Any]) -> str:
  """Save prompt version with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_prompt = _validate_and_sanitize_input(prompt, "save_prompt_version")
    sanitized_prompt.setdefault("_type", "prompt_version")
    
    res = await db["prompt_versions"].insert_one(sanitized_prompt)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "prompt_versions", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving prompt version: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "prompt_versions", "error": str(e)},
        "ERROR"
    )
    raise

async def save_voice_session(session: Dict[str, Any]) -> str:
  """Save voice session with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_session = _validate_and_sanitize_input(session, "save_voice_session")
    sanitized_session.setdefault("_type", "voice_session")
    
    res = await db["voice_sessions"].insert_one(sanitized_session)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "voice_sessions", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving voice session: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "voice_sessions", "error": str(e)},
        "ERROR"
    )
    raise

async def save_partner_api_call(api_call: Dict[str, Any]) -> str:
  """Save partner API call with input validation and sanitization"""
  try:
    db = await get_db()
    sanitized_api_call = _validate_and_sanitize_input(api_call, "save_partner_api_call")
    sanitized_api_call.setdefault("_type", "partner_api_call")
    
    res = await db["partner_api_calls"].insert_one(sanitized_api_call)
    
    audit_logger.log_security_event(
        "DB_INSERT_SUCCESS",
        "system",
        {"collection": "partner_api_calls", "id": str(res.inserted_id)},
        "INFO"
    )
    
    return str(res.inserted_id)
  except Exception as e:
    logger.error(f"Error saving partner API call: {e}")
    audit_logger.log_security_event(
        "DB_INSERT_FAILED",
        "system",
        {"collection": "partner_api_calls", "error": str(e)},
        "ERROR"
    )
    raise

async def get_prompt_version(agent_name: str, skill_name: str, version: str = "latest") -> Dict[str, Any]:
  """Get prompt version with input validation and sanitization"""
  try:
    # Validate and sanitize input parameters
    validated_agent_name = security_validator.sanitize_string(agent_name, max_length=100)
    validated_skill_name = security_validator.sanitize_string(skill_name, max_length=100)
    validated_version = security_validator.sanitize_string(version, max_length=50)
    
    db = await get_db()
    
    # Sanitize query parameters
    query = {"agent": validated_agent_name, "skill": validated_skill_name}
    
    if validated_version == "latest":
      doc = await db["prompt_versions"].find_one(
        query,
        sort=[("version", -1)]
      )
    else:
      query["version"] = validated_version
      doc = await db["prompt_versions"].find_one(query)
    
    audit_logger.log_security_event(
        "DB_QUERY_SUCCESS",
        "system",
        {"collection": "prompt_versions", "query": str(query)},
        "INFO"
    )
    
    return doc or {}
  except Exception as e:
    logger.error(f"Error getting prompt version: {e}")
    audit_logger.log_security_event(
        "DB_QUERY_FAILED",
        "system",
        {"collection": "prompt_versions", "error": str(e)},
        "ERROR"
    )
    raise

async def get_ab_test_prompts(agent_name: str, skill_name: str, test_id: str) -> list[Dict[str, Any]]:
  """Get AB test prompts with input validation and sanitization"""
  try:
    # Validate and sanitize input parameters
    validated_agent_name = security_validator.sanitize_string(agent_name, max_length=100)
    validated_skill_name = security_validator.sanitize_string(skill_name, max_length=100)
    validated_test_id = security_validator.sanitize_string(test_id, max_length=100)
    
    db = await get_db()
    
    # Sanitize query parameters
    query = {
      "agent": validated_agent_name, 
      "skill": validated_skill_name, 
      "ab_test_id": validated_test_id
    }
    
    cursor = db["prompt_versions"].find(query)
    result = await cursor.to_list(length=None)
    
    audit_logger.log_security_event(
        "DB_QUERY_SUCCESS",
        "system",
        {"collection": "prompt_versions", "query": str(query), "result_count": len(result)},
        "INFO"
    )
    
    return result
  except Exception as e:
    logger.error(f"Error getting AB test prompts: {e}")
    audit_logger.log_security_event(
        "DB_QUERY_FAILED",
        "system",
        {"collection": "prompt_versions", "error": str(e)},
        "ERROR"
    )
    raise
