"""
Enhanced Agent Base Class for AI Career Copilot
Integrates RAG capabilities and hallucination detection to reduce hallucinations.
"""

import logging
import json
import asyncio
from typing import Any, AsyncIterable, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# Fix import paths to use relative imports
from .rag_manager import RAGManager, RAGResponse, SearchResult
from .hallucination_detector import HallucinationDetector, HallucinationReport
from .azure_services import AzureServicesManager
from .config import load_config

logger = logging.getLogger(__name__)

@dataclass
class EnhancedAgentConfig:
    """Configuration for enhanced agents"""
    enable_rag: bool = True
    enable_hallucination_detection: bool = True
    enable_source_attribution: bool = True
    enable_confidence_scoring: bool = True
    enable_fact_checking: bool = True
    min_confidence_threshold: float = 0.7
    max_retrieved_context: int = 5
    context_type: str = "general"
    require_sources: bool = False

@dataclass
class EnhancedResponse:
    """Enhanced response with RAG and hallucination detection"""
    content: str
    original_content: str
    sources: List[SearchResult]
    confidence_score: float
    hallucination_report: Optional[HallucinationReport] = None
    rag_metadata: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

class EnhancedAgentBase(ABC):
    """Base class for agents with enhanced RAG and hallucination detection capabilities"""
    
    def __init__(self, config: EnhancedAgentConfig = None):
        self.config = config or EnhancedAgentConfig()
        self.rag_manager: Optional[RAGManager] = None
        self.hallucination_detector: Optional[HallucinationDetector] = None
        self.azure_services: Optional[AzureServicesManager] = None
        
        # Initialize services if available
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Azure services and RAG components"""
        try:
            # Load configuration
            app_config = load_config()
            
            # Initialize Azure services with config
            self.azure_services = AzureServicesManager(app_config)
            
            # Initialize RAG manager if enabled
            if self.config.enable_rag and self.azure_services.is_ai_search_available():
                self.rag_manager = RAGManager(self.azure_services)
                logger.info("RAG manager initialized successfully")
            
            # Initialize hallucination detector if enabled
            if self.config.enable_hallucination_detection:
                self.hallucination_detector = HallucinationDetector()
                logger.info("Hallucination detector initialized successfully")
                
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced services: {e}")
            # Continue without enhanced features
    
    async def invoke_enhanced(
        self, 
        query: str, 
        session_id: str,
        context_type: str = None,
        additional_context: str = None
    ) -> EnhancedResponse:
        """Enhanced invoke method with RAG and hallucination detection"""
        try:
            # Validate inputs
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            if not session_id or not session_id.strip():
                raise ValueError("Session ID cannot be empty")
            
            # 1. Retrieve relevant context using RAG
            retrieved_context = []
            if self.config.enable_rag and self.rag_manager:
                context_type = context_type or self.config.context_type
                retrieved_context = await self.rag_manager.retrieve_relevant_context(
                    query, context_type
                )
                logger.info(f"Retrieved {len(retrieved_context)} relevant context chunks")
            
            # 2. Generate base response using the original agent logic
            base_response = await self._invoke_base(query, session_id)
            
            # 3. Enhance response with RAG context if available
            enhanced_content = base_response
            if retrieved_context and self.config.enable_rag:
                enhanced_content = await self._enhance_with_rag(
                    query, base_response, retrieved_context, additional_context
                )
            
            # 4. Perform hallucination detection
            hallucination_report = None
            if self.config.enable_hallucination_detection and self.hallucination_detector:
                hallucination_report = await self.hallucination_detector.analyze_response(
                    enhanced_content, query, 
                    sources=[self._convert_to_source_dict(ctx) for ctx in retrieved_context],
                    context=additional_context
                )
                logger.info(f"Hallucination analysis completed: {hallucination_report.overall_risk} risk")
            
            # 5. Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                retrieved_context, hallucination_report, enhanced_content
            )
            
            # 6. Validate confidence threshold
            if self.config.require_sources and confidence_score < self.config.min_confidence_threshold:
                enhanced_content = self._generate_low_confidence_response(
                    query, retrieved_context, confidence_score
                )
            
            # 7. Add source attribution
            if self.config.enable_source_attribution:
                enhanced_content = self._add_source_attribution(
                    enhanced_content, retrieved_context
                )
            
            return EnhancedResponse(
                content=enhanced_content,
                original_content=base_response,
                sources=retrieved_context,
                confidence_score=confidence_score,
                hallucination_report=hallucination_report,
                rag_metadata={
                    'context_retrieved': len(retrieved_context),
                    'context_type': context_type or self.config.context_type,
                    'rag_enabled': self.config.enable_rag
                },
                metadata={
                    'session_id': session_id,
                    'query': query,
                    'generated_at': datetime.utcnow().isoformat(),
                    'agent_name': self.__class__.__name__
                }
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced invoke: {e}")
            return self._create_error_response(query, str(e))
    
    async def stream_enhanced(
        self, 
        query: str, 
        session_id: str,
        context_type: str = None,
        additional_context: str = None
    ) -> AsyncIterable[Dict[str, Any]]:
        """Enhanced streaming method with RAG and hallucination detection"""
        try:
            # Validate inputs
            if not query or not query.strip():
                yield {"is_task_complete": True, "content": "Error: Query cannot be empty", "error": True}
                return
            if not session_id or not session_id.strip():
                yield {"is_task_complete": True, "content": "Error: Session ID cannot be empty", "error": True}
                return
            
            # 1. Retrieve context (non-streaming)
            retrieved_context = []
            if self.config.enable_rag and self.rag_manager:
                context_type = context_type or self.config.context_type
                retrieved_context = await self.rag_manager.retrieve_relevant_context(
                    query, context_type
                )
                yield {
                    "is_task_complete": False,
                    "updates": f"Retrieved {len(retrieved_context)} relevant context chunks",
                    "metadata": {"context_retrieved": len(retrieved_context)}
                }
            
            # 2. Stream base response
            async for chunk in self._stream_base(query, session_id):
                yield chunk
            
            # 3. Perform post-streaming analysis
            if self.config.enable_hallucination_detection and self.hallucination_detector:
                # Get the final response for analysis
                final_response = await self._invoke_base(query, session_id)
                
                hallucination_report = await self.hallucination_detector.analyze_response(
                    final_response, query,
                    sources=[self._convert_to_source_dict(ctx) for ctx in retrieved_context],
                    context=additional_context
                )
                
                confidence_score = self._calculate_confidence_score(
                    retrieved_context, hallucination_report, final_response
                )
                
                yield {
                    "is_task_complete": True,
                    "content": final_response,
                    "hallucination_analysis": {
                        "risk_level": hallucination_report.overall_risk,
                        "risk_score": hallucination_report.risk_score,
                        "confidence_score": confidence_score,
                        "recommendations": hallucination_report.recommendations
                    },
                    "sources": [self._convert_to_source_dict(ctx) for ctx in retrieved_context]
                }
            else:
                yield {
                    "is_task_complete": True,
                    "content": "Response completed",
                    "sources": [self._convert_to_source_dict(ctx) for ctx in retrieved_context]
                }
                
        except Exception as e:
            logger.error(f"Error in enhanced streaming: {e}")
            yield {
                "is_task_complete": True,
                "content": f"Error: {str(e)}",
                "error": True
            }
    
    @abstractmethod
    async def _invoke_base(self, query: str, session_id: str) -> str:
        """Base invoke method to be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _stream_base(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Base streaming method to be implemented by subclasses"""
        pass
    
    async def _enhance_with_rag(
        self, 
        query: str, 
        base_response: str, 
        retrieved_context: List[SearchResult],
        additional_context: str = None
    ) -> str:
        """Enhance base response with RAG context"""
        try:
            if not retrieved_context:
                return base_response
            
            # Create enhanced prompt with RAG context
            context_text = self._prepare_context_for_enhancement(retrieved_context)
            
            enhanced_prompt = f"""You are an AI agent. Use the following context to enhance your response. 
            If the context provides additional relevant information, incorporate it. 
            If not, keep your original response but ensure it's accurate.

            QUERY: {query}
            ORIGINAL RESPONSE: {base_response}
            
            RELEVANT CONTEXT:
            {context_text}
            
            ENHANCED RESPONSE (incorporate relevant context when available):"""
            
            # For now, return a simple enhancement
            # In production, this would be sent to the LLM
            if retrieved_context:
                source_info = f"\n\nSources: {len(retrieved_context)} relevant documents retrieved"
                return base_response + source_info
            
            return base_response
            
        except Exception as e:
            logger.error(f"Error enhancing with RAG: {e}")
            return base_response
    
    def _prepare_context_for_enhancement(self, retrieved_context: List[SearchResult]) -> str:
        """Prepare retrieved context for enhancement"""
        if not retrieved_context:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(retrieved_context[:3]):  # Limit to top 3
            context_parts.append(f"Source {i+1} (Score: {result.relevance_score:.2f}):\n{result.content[:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence_score(
        self, 
        retrieved_context: List[SearchResult],
        hallucination_report: Optional[HallucinationReport],
        response_content: str
    ) -> float:
        """Calculate overall confidence score"""
        try:
            # Base confidence from context availability
            context_confidence = min(1.0, len(retrieved_context) / self.config.max_retrieved_context)
            
            # Hallucination risk factor
            hallucination_factor = 1.0
            if hallucination_report:
                hallucination_factor = 1.0 - hallucination_report.risk_score
            
            # Content quality factor (simple heuristic)
            content_quality = min(1.0, len(response_content) / 100)  # Normalize to 100 chars
            
            # Weighted combination
            confidence = (
                context_confidence * 0.4 +
                hallucination_factor * 0.4 +
                content_quality * 0.2
            )
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _generate_low_confidence_response(
        self, 
        query: str, 
        retrieved_context: List[SearchResult],
        confidence_score: float
    ) -> str:
        """Generate a response when confidence is too low"""
        if retrieved_context:
            return f"""I found some information that might be relevant to your query, but I'm not confident enough to provide a complete answer.

Query: {query}

Available context: {len(retrieved_context)} documents retrieved
Confidence level: {confidence_score:.2f}

I recommend:
1. Reviewing the source documents directly
2. Providing more specific details in your query
3. Consulting with a human expert for critical decisions

This helps ensure accuracy and reduces the risk of providing incorrect information."""
        else:
            return f"""I don't have enough information to provide a confident answer to your query.

Query: {query}
Confidence level: {confidence_score:.2f}

To help you better, please:
1. Provide more context or details
2. Specify what type of information you need
3. Consider rephrasing your question

I want to ensure I provide accurate, helpful information rather than making assumptions."""
    
    def _add_source_attribution(self, content: str, sources: List[SearchResult]) -> str:
        """Add source attribution to the response"""
        if not sources or not self.config.enable_source_attribution:
            return content
        
        attribution_text = "\n\n--- Sources ---\n"
        for i, source in enumerate(sources[:3]):  # Limit to top 3 sources
            source_id = source.document_id or f"Source {i+1}"
            relevance = f" (Relevance: {source.relevance_score:.2f})"
            attribution_text += f"{i+1}. {source_id}{relevance}\n"
        
        return content + attribution_text
    
    def _convert_to_source_dict(self, search_result: SearchResult) -> Dict[str, Any]:
        """Convert SearchResult to dictionary format"""
        return {
            'id': search_result.document_id,
            'content': search_result.content,
            'metadata': search_result.metadata,
            'relevance_score': search_result.relevance_score,
            'source_url': search_result.source_url,
            'chunk_id': search_result.chunk_id
        }
    
    def _create_error_response(self, query: str, error_message: str) -> EnhancedResponse:
        """Create an error response"""
        return EnhancedResponse(
            content=f"Error processing request: {error_message}",
            original_content="",
            sources=[],
            confidence_score=0.0,
            hallucination_report=None,
            rag_metadata={'error': error_message},
            metadata={
                'query': query,
                'error': True,
                'error_message': error_message,
                'generated_at': datetime.utcnow().isoformat()
            }
        )
    
    async def ingest_knowledge(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Ingest knowledge into the RAG system"""
        try:
            if not self.config.enable_rag or not self.rag_manager:
                logger.warning("RAG not enabled or RAG manager not available")
                return False
            
            success = await self.rag_manager.ingest_document(content, metadata)
            if success:
                logger.info(f"Successfully ingested knowledge: {metadata.get('title', 'Unknown')}")
            return success
            
        except Exception as e:
            logger.error(f"Error ingesting knowledge: {e}")
            return False
    
    async def search_knowledge(self, query: str, filters: Optional[str] = None) -> Dict[str, Any]:
        """Search the knowledge base"""
        try:
            if not self.config.enable_rag or not self.rag_manager:
                return {'error': 'RAG not enabled'}
            
            return await self.rag_manager.search_knowledge_base(query, filters)
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return {'error': str(e)}
    
    def get_enhanced_capabilities(self) -> Dict[str, Any]:
        """Get information about enhanced capabilities"""
        return {
            'rag_enabled': self.config.enable_rag and self.rag_manager is not None,
            'hallucination_detection_enabled': self.config.enable_hallucination_detection,
            'source_attribution_enabled': self.config.enable_source_attribution,
            'confidence_scoring_enabled': self.config.enable_confidence_scoring,
            'fact_checking_enabled': self.config.enable_fact_checking,
            'azure_services_available': self.azure_services is not None,
            'ai_search_available': self.azure_services.is_ai_search_available() if self.azure_services else False,
            'blob_storage_available': self.azure_services.is_blob_storage_available() if self.azure_services else False
        }
    
    def update_config(self, **kwargs):
        """Update agent configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config: {key} = {value}")
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            if not self.config.enable_rag or not self.rag_manager:
                return {'error': 'RAG not enabled'}
            
            return await self.rag_manager.get_knowledge_base_stats()
            
        except Exception as e:
            logger.error(f"Error getting knowledge stats: {e}")
            return {'error': str(e)}
