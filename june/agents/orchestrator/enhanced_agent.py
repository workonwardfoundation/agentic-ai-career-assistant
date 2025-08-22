"""
Enhanced Orchestrator Agent with RAG and Hallucination Detection
Demonstrates how to reduce hallucinations using the enhanced agent framework.
"""

import logging
import json
from typing import Any, AsyncIterable, Dict, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

# Fix import path to use correct relative imports
from common.utils.enhanced_agent_base import EnhancedAgentBase, EnhancedAgentConfig, EnhancedResponse

logger = logging.getLogger(__name__)

class EnhancedOrchestratorAgent(EnhancedAgentBase):
    """Enhanced Orchestrator Agent with RAG and hallucination detection"""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self, config: EnhancedAgentConfig = None):
        # Initialize enhanced capabilities
        super().__init__(config)
        
        # Initialize Google ADK components
        self._agent = self._build_agent()
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        self._user_id = "enhanced_orchestrator"
        
        # Note: _load_initial_knowledge is now called separately since it's async
    
    async def initialize(self):
        """Async initialization method to load knowledge base"""
        await self._load_initial_knowledge()
    
    def _build_agent(self) -> LlmAgent:
        """Build the LLM agent with enhanced instructions"""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="enhanced_orchestrator",
            description="Enhanced orchestrator with RAG capabilities and hallucination detection.",
            instruction=(
                "You are an AI career planning assistant. Plan daily job-search workflows based on available information. "
                "IMPORTANT: Only make claims that you can support with evidence. If you're unsure about something, "
                "acknowledge the uncertainty. Use phrases like 'based on available information' and 'according to sources' "
                "when referencing information. Avoid absolute statements like 'always', 'never', 'everyone' unless you have "
                "definitive proof. Your goal is to provide accurate, helpful guidance while being transparent about "
                "what you know and what you don't."
            ),
            tools=[],
        )
    
    async def _load_initial_knowledge(self):
        """Load initial knowledge base with career planning information"""
        try:
            if not self.config.enable_rag:
                return
            
            # Sample career planning knowledge
            career_knowledge = [
                {
                    "title": "Job Search Best Practices",
                    "content": "Effective job searching involves multiple strategies: networking (70% of jobs are found through connections), online applications (20%), and direct outreach (10%). The average job search takes 3-6 months. Key success factors include having a targeted resume, practicing interview skills, and maintaining a consistent daily routine.",
                    "document_type": "career_guidance",
                    "tags": ["job_search", "best_practices", "statistics"]
                },
                {
                    "title": "LinkedIn Optimization",
                    "content": "LinkedIn profiles with professional photos receive 21x more profile views. Complete profiles get 40x more opportunities. Key optimization areas include: compelling headline, detailed experience descriptions, relevant skills, and active engagement with industry content.",
                    "document_type": "career_guidance",
                    "tags": ["linkedin", "optimization", "social_media"]
                },
                {
                    "title": "Resume Writing Guidelines",
                    "content": "ATS-friendly resumes should use standard section headers, include relevant keywords, and avoid graphics. The average recruiter spends 6-7 seconds reviewing a resume. Quantify achievements with specific numbers and metrics. Keep to 1-2 pages maximum.",
                    "document_type": "career_guidance",
                    "tags": ["resume", "ats", "writing"]
                },
                {
                    "title": "Interview Preparation",
                    "content": "Successful interview preparation includes researching the company, practicing common questions, preparing STAR method responses, and having thoughtful questions ready. Mock interviews can improve performance by 30%. Follow up within 24 hours after interviews.",
                    "document_type": "career_guidance",
                    "tags": ["interview", "preparation", "follow_up"]
                },
                {
                    "title": "Salary Negotiation",
                    "content": "Salary negotiation can increase initial offers by 5-15%. Research market rates using tools like Glassdoor and Payscale. Focus on value and achievements rather than personal needs. Consider total compensation including benefits, equity, and growth opportunities.",
                    "document_type": "career_guidance",
                    "tags": ["salary", "negotiation", "compensation"]
                }
            ]
            
            # Ingest knowledge into RAG system
            for knowledge in career_knowledge:
                await self.ingest_knowledge(
                    content=knowledge["content"],
                    metadata={
                        "title": knowledge["title"],
                        "document_type": knowledge["document_type"],
                        "tags": knowledge["tags"],
                        "agent_name": "enhanced_orchestrator",
                        "user_id": "system",
                        "created_at": "2024-12-19T00:00:00Z"
                    }
                )
            
            logger.info("Initial career knowledge loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load initial knowledge: {e}")
    
    async def _invoke_base(self, query: str, session_id: str) -> str:
        """Base invoke method using Google ADK"""
        try:
            content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
            events = self._runner.run(user_id=self._user_id, session_id=session_id, new_message=content)
            
            if not events or not events[-1].content or not events[-1].content.parts:
                return ""
            
            return "\n".join([p.text for p in events[-1].content.parts if p.text])
            
        except Exception as e:
            logger.error(f"Error in base invoke: {e}")
            return f"Error processing request: {str(e)}"
    
    async def _stream_base(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Base streaming method using Google ADK"""
        try:
            content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
            
            async for event in self._runner.run_async(user_id=self._user_id, session_id=session_id, new_message=content):
                if event.is_final_response():
                    response = ""
                    if event.content and event.content.parts and event.content.parts[0].text:
                        response = "\n".join([p.text for p in event.content.parts if p.text])
                    yield {"is_task_complete": True, "content": response}
                else:
                    yield {"is_task_complete": False, "updates": "Planning your enhanced workflow..."}
                    
        except Exception as e:
            logger.error(f"Error in base streaming: {e}")
            yield {"is_task_complete": True, "content": f"Error: {str(e)}"}
    
    async def plan_workflow_enhanced(
        self, 
        query: str, 
        session_id: str,
        user_profile: Dict[str, Any] = None
    ) -> EnhancedResponse:
        """Enhanced workflow planning with RAG and hallucination detection"""
        try:
            # Create context-specific query
            context_query = self._create_context_query(query, user_profile)
            
            # Use enhanced invoke
            enhanced_response = await self.invoke_enhanced(
                query=context_query,
                session_id=session_id,
                context_type="career_guidance",
                additional_context=json.dumps(user_profile) if user_profile else None
            )
            
            # Add workflow-specific metadata
            enhanced_response.metadata.update({
                "workflow_type": "career_planning",
                "user_profile_provided": user_profile is not None,
                "enhanced_features_used": True
            })
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error in enhanced workflow planning: {e}")
            return self._create_error_response(query, str(e))
    
    def _create_context_query(self, query: str, user_profile: Dict[str, Any] = None) -> str:
        """Create a context-rich query for better RAG retrieval"""
        base_query = query
        
        if user_profile:
            profile_context = f"User Profile: {json.dumps(user_profile, default=str)}"
            base_query = f"{query}\n\nContext: {profile_context}"
        
        return base_query
    
    async def get_career_insights(self, topic: str, session_id: str) -> EnhancedResponse:
        """Get career insights with RAG enhancement"""
        try:
            query = f"Provide insights and best practices for: {topic}"
            
            enhanced_response = await self.invoke_enhanced(
                query=query,
                session_id=session_id,
                context_type="career_guidance"
            )
            
            # Add insights-specific metadata
            enhanced_response.metadata.update({
                "insight_topic": topic,
                "response_type": "career_insights"
            })
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error getting career insights: {e}")
            return self._create_error_response(query, str(e))
    
    async def validate_career_advice(
        self, 
        advice: str, 
        session_id: str
    ) -> Dict[str, Any]:
        """Validate career advice against knowledge base"""
        try:
            # Search knowledge base for relevant information
            search_results = await self.search_knowledge(advice, filters="document_type eq 'career_guidance'")
            
            # Analyze advice for potential issues
            if self.hallucination_detector:
                analysis = await self.hallucination_detector.analyze_response(
                    advice, 
                    query="Validate career advice",
                    sources=search_results.get('documents', [])
                )
                
                return {
                    "advice": advice,
                    "validation_results": {
                        "risk_level": analysis.overall_risk,
                        "risk_score": analysis.risk_score,
                        "flagged_claims": analysis.flagged_claims,
                        "recommendations": analysis.recommendations
                    },
                    "supporting_sources": len(search_results.get('documents', [])),
                    "confidence": "high" if analysis.overall_risk == "low" else "medium" if analysis.overall_risk == "medium" else "low"
                }
            else:
                return {
                    "advice": advice,
                    "validation_results": "Hallucination detection not available",
                    "supporting_sources": len(search_results.get('documents', [])),
                    "confidence": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Error validating career advice: {e}")
            return {
                "advice": advice,
                "error": str(e),
                "confidence": "error"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status including enhanced capabilities"""
        base_status = {
            "agent_name": "Enhanced Orchestrator",
            "status": "active",
            "model": "gemini-2.0-flash-001",
            "supported_content_types": self.SUPPORTED_CONTENT_TYPES
        }
        
        # Add enhanced capabilities status
        enhanced_capabilities = self.get_enhanced_capabilities()
        base_status["enhanced_capabilities"] = self.get_enhanced_capabilities()
        
        # Add knowledge base stats if available
        if self.config.enable_rag:
            try:
                # This would be async in practice, but for status we'll handle it differently
                base_status["knowledge_base"] = {
                    "rag_enabled": True,
                    "status": "available" if self.rag_manager else "unavailable"
                }
            except:
                base_status["knowledge_base"] = {"rag_enabled": True, "status": "error"}
        
        return base_status
    
    async def update_knowledge_base(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Update the knowledge base with new information"""
        try:
            if not self.config.enable_rag:
                logger.warning("RAG not enabled, cannot update knowledge base")
                return False
            
            success = await self.ingest_knowledge(content, metadata)
            
            if success:
                logger.info(f"Successfully updated knowledge base with: {metadata.get('title', 'Unknown')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            return False
    
    def get_enhancement_recommendations(self) -> List[str]:
        """Get recommendations for improving agent performance"""
        recommendations = []
        
        if not self.config.enable_rag:
            recommendations.append("Enable RAG to provide more accurate, source-based responses")
        
        if not self.config.enable_hallucination_detection:
            recommendations.append("Enable hallucination detection to identify potential accuracy issues")
        
        if not self.config.enable_source_attribution:
            recommendations.append("Enable source attribution to improve transparency and credibility")
        
        if self.config.min_confidence_threshold > 0.8:
            recommendations.append("Consider lowering confidence threshold for more informative responses")
        
        if not recommendations:
            recommendations.append("All enhancement features are enabled. Monitor performance metrics for further optimization.")
        
        return recommendations
