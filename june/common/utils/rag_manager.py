"""
RAG (Retrieval Augmented Generation) Manager for AI Career Copilot
Implements advanced techniques to reduce hallucinations and improve response accuracy.
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
import re

from .azure_ai_search import AzureAISearchClient
from .azure_blob_storage import AzureBlobStorageClient
from .azure_services import AzureServicesManager

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of document content"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    chunk_index: int = 0
    total_chunks: int = 1

@dataclass
class SearchResult:
    """Represents a search result with relevance information"""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    source_url: Optional[str] = None
    chunk_id: Optional[str] = None

@dataclass
class RAGResponse:
    """Represents a RAG-enhanced response"""
    content: str
    sources: List[SearchResult]
    confidence_score: float
    fact_check_results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DocumentProcessor:
    """Handles document processing and chunking"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split text into overlapping chunks"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if not metadata:
            raise ValueError("Metadata cannot be empty")
            
        chunks = []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into sentences first to maintain context
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk
                chunk = self._create_chunk(current_chunk, metadata, chunk_index, len(sentences))
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(current_chunk, metadata, chunk_index, len(sentences))
            chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with chunking
        text = re.sub(r'[^\w\s\.\!\?\-]', '', text)
        return text.strip()
    
    def _create_chunk(self, content: str, metadata: Dict[str, Any], chunk_index: int, total_chunks: int) -> DocumentChunk:
        """Create a document chunk with metadata"""
        if not content:
            raise ValueError("Content cannot be empty")
            
        chunk_id = f"{metadata.get('document_id', 'unknown')}_chunk_{chunk_index}"
        
        chunk_metadata = metadata.copy()
        chunk_metadata.update({
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'chunk_size': len(content),
            'processed_at': datetime.now(timezone.utc).isoformat()
        })
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            metadata=chunk_metadata,
            chunk_index=chunk_index,
            total_chunks=total_chunks
        )

class EmbeddingManager:
    """Manages document embeddings for semantic search"""
    
    def __init__(self, azure_services: AzureServicesManager):
        if not azure_services:
            raise ValueError("Azure services manager cannot be None")
        self.azure_services = azure_services
        self.embedding_model = "text-embedding-3-small"  # 1536 dimensions
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using Azure OpenAI"""
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return []
            
        try:
            # This would integrate with Azure OpenAI embedding service
            # For now, return a placeholder
            logger.info(f"Generating embeddings for text of length {len(text)}")
            
            # TODO: Implement actual embedding generation
            # response = await self.azure_services.openai_client.embeddings.create(
            #     model=self.embedding_model,
            #     input=text
            # )
            # return response.data[0].embedding
            
            # Placeholder: return random vector for now
            import random
            random.seed(hash(text) % 2**32)
            return [random.uniform(-1, 1) for _ in range(1536)]
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch"""
        if not texts:
            return []
            
        embeddings = []
        for text in texts:
            embedding = await self.generate_embeddings(text)
            embeddings.append(embedding)
        return embeddings

class RAGManager:
    """Main RAG manager that orchestrates retrieval and generation"""
    
    def __init__(self, azure_services: AzureServicesManager):
        if not azure_services:
            raise ValueError("Azure services manager cannot be None")
            
        self.azure_services = azure_services
        self.document_processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager(azure_services)
        
        # Initialize Azure services
        self.search_client = azure_services.ai_search
        self.blob_storage = azure_services.blob_storage
        
        # RAG configuration
        self.max_retrieved_chunks = 5
        self.min_relevance_score = 0.7
        self.enable_fact_checking = True
    
    async def ingest_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Ingest a document into the RAG system"""
        if not content or not content.strip():
            logger.error("Cannot ingest empty document content")
            return False
        if not metadata:
            logger.error("Cannot ingest document without metadata")
            return False
            
        try:
            # Generate document ID
            document_id = self._generate_document_id(content, metadata)
            metadata['document_id'] = document_id
            metadata['ingested_at'] = datetime.now(timezone.utc).isoformat()
            
            # Process and chunk document
            chunks = self.document_processor.chunk_text(content, metadata)
            
            # Generate embeddings for chunks
            for chunk in chunks:
                chunk.embedding = await self.embedding_manager.generate_embeddings(chunk.content)
            
            # Store chunks in Azure AI Search
            success = await self._store_chunks_in_search(chunks)
            
            # Store original document in blob storage
            if success and self.blob_storage:
                blob_metadata = {
                    'document_id': document_id,
                    'chunk_count': len(chunks),
                    'ingested_at': metadata['ingested_at']
                }
                self.blob_storage.upload_data(
                    f"documents/{document_id}.json",
                    json.dumps({'content': content, 'metadata': metadata}),
                    metadata=blob_metadata
                )
            
            logger.info(f"Successfully ingested document {document_id} with {len(chunks)} chunks")
            return success
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            return False
    
    async def retrieve_relevant_context(self, query: str, context_type: str = "general") -> List[SearchResult]:
        """Retrieve relevant context for a query"""
        if not query or not query.strip():
            logger.warning("Empty query provided for context retrieval")
            return []
        if not context_type or not context_type.strip():
            context_type = "general"
            
        try:
            # Generate query embedding
            query_embedding = await self.embedding_manager.generate_embeddings(query)
            
            # Search for relevant documents
            search_results = self.search_client.search_documents(
                query=query,
                vector_embedding=query_embedding,
                filters=f"document_type eq '{context_type}'" if context_type != "general" else None,
                top=self.max_retrieved_chunks
            )
            
            # Process and filter results
            relevant_results = []
            for doc in search_results.get('documents', []):
                if doc.get('score', 0) >= self.min_relevance_score:
                    result = SearchResult(
                        document_id=doc.get('id'),
                        content=doc.get('content', ''),
                        metadata=doc,
                        relevance_score=doc.get('score', 0),
                        source_url=doc.get('source_url'),
                        chunk_id=doc.get('id')
                    )
                    relevant_results.append(result)
            
            # Sort by relevance score
            relevant_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Retrieved {len(relevant_results)} relevant chunks for query: {query[:100]}...")
            return relevant_results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    async def generate_rag_response(
        self, 
        query: str, 
        agent_context: str,
        context_type: str = "general"
    ) -> RAGResponse:
        """Generate a RAG-enhanced response with source attribution"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not agent_context or not agent_context.strip():
            agent_context = "No agent context provided"
            
        try:
            # Retrieve relevant context
            relevant_context = await self.retrieve_relevant_context(query, context_type)
            
            # Prepare context for LLM
            context_text = self._prepare_context_for_llm(relevant_context)
            
            # Generate enhanced prompt
            enhanced_prompt = self._create_enhanced_prompt(query, agent_context, context_text)
            
            # TODO: This would be sent to the LLM for generation
            # For now, return a structured response
            response_content = f"Based on the available information: {query}\n\nContext: {context_text[:200]}..."
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(relevant_context, query)
            
            # Perform fact checking if enabled
            fact_check_results = []
            if self.enable_fact_checking:
                fact_check_results = await self._perform_fact_checking(response_content, relevant_context)
            
            return RAGResponse(
                content=response_content,
                sources=relevant_context,
                confidence_score=confidence_score,
                fact_check_results=fact_check_results,
                metadata={
                    'query': query,
                    'context_type': context_type,
                    'retrieved_chunks': len(relevant_context),
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return RAGResponse(
                content=f"Error generating response: {str(e)}",
                sources=[],
                confidence_score=0.0,
                fact_check_results=[],
                metadata={'error': str(e)}
            )
    
    def _generate_document_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID"""
        if not content:
            raise ValueError("Content cannot be empty for document ID generation")
            
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"doc_{content_hash[:8]}_{timestamp}"
    
    async def _store_chunks_in_search(self, chunks: List[DocumentChunk]) -> bool:
        """Store document chunks in Azure AI Search"""
        if not chunks:
            logger.warning("No chunks to store in search")
            return True
            
        try:
            for chunk in chunks:
                # Prepare document for indexing
                search_document = {
                    'id': chunk.id,
                    'content': chunk.content,
                    'content_vector': chunk.embedding,
                    'document_type': chunk.metadata.get('document_type', 'general'),
                    'agent_name': chunk.metadata.get('agent_name', 'unknown'),
                    'user_id': chunk.metadata.get('user_id', 'unknown'),
                    'title': chunk.metadata.get('title', ''),
                    'summary': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    'created_at': chunk.metadata.get('created_at', datetime.now(timezone.utc).isoformat()),
                    'updated_at': chunk.metadata.get('updated_at', datetime.now(timezone.utc).isoformat()),
                    'tags': chunk.metadata.get('tags', []),
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks
                }
                
                # Index the document
                success = self.search_client.index_document(search_document)
                if not success:
                    logger.error(f"Failed to index chunk {chunk.id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing chunks in search: {e}")
            return False
    
    def _prepare_context_for_llm(self, search_results: List[SearchResult]) -> str:
        """Prepare retrieved context for LLM consumption"""
        if not search_results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"Source {i+1} (Score: {result.relevance_score:.2f}):\n{result.content}")
        
        return "\n\n".join(context_parts)
    
    def _create_enhanced_prompt(self, query: str, agent_context: str, context_text: str) -> str:
        """Create an enhanced prompt with RAG context"""
        return f"""You are an AI agent with access to relevant information. Use ONLY the provided context to answer the query. If the context doesn't contain enough information, say so clearly.

AGENT CONTEXT: {agent_context}

RELEVANT CONTEXT:
{context_text}

QUERY: {query}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. If you need to make assumptions, state them clearly
3. Cite specific sources when possible
4. If the context is insufficient, say "I don't have enough information to answer this question accurately"
5. Do not make up information not present in the context

RESPONSE:"""
    
    def _calculate_confidence_score(self, search_results: List[SearchResult], query: str) -> float:
        """Calculate confidence score based on context relevance and coverage"""
        if not search_results:
            return 0.0
        
        try:
            # Average relevance score
            avg_relevance = sum(r.relevance_score for r in search_results) / len(search_results)
            
            # Coverage score (how much context we have)
            total_content_length = sum(len(r.content) for r in search_results)
            coverage_score = min(1.0, total_content_length / 5000)  # Normalize to 5000 chars
            
            # Query-specific scoring
            query_words = set(query.lower().split())
            context_words = set(' '.join(r.content.lower() for r in search_results).split())
            word_overlap = len(query_words.intersection(context_words)) / max(len(query_words), 1)
            
            # Weighted combination
            confidence = (avg_relevance * 0.5 + coverage_score * 0.3 + word_overlap * 0.2)
            
            return min(1.0, max(0.0, confidence))
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0
    
    async def _perform_fact_checking(self, response: str, sources: List[SearchResult]) -> List[Dict[str, Any]]:
        """Perform basic fact checking against sources"""
        if not response or not sources:
            return []
            
        fact_check_results = []
        
        # Extract claims from response
        claims = self._extract_claims(response)
        
        for claim in claims:
            # Check if claim is supported by sources
            support_found = False
            supporting_sources = []
            
            for source in sources:
                if self._claim_supported_by_source(claim, source.content):
                    support_found = True
                    supporting_sources.append(source.document_id)
            
            fact_check_results.append({
                'claim': claim,
                'supported': support_found,
                'supporting_sources': supporting_sources,
                'confidence': 'high' if support_found else 'low'
            })
        
        return fact_check_results
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        if not text:
            return []
            
        # Simple claim extraction - look for statements that could be facts
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                # Look for sentences that might contain facts
                if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'had']):
                    claims.append(sentence)
        
        return claims[:5]  # Limit to 5 claims
    
    def _claim_supported_by_source(self, claim: str, source_content: str) -> bool:
        """Check if a claim is supported by source content"""
        if not claim or not source_content:
            return False
            
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        source_words = set(re.findall(r'\b\w+\b', source_content.lower()))
        
        # Calculate word overlap
        overlap = len(claim_words.intersection(source_words))
        overlap_ratio = overlap / max(len(claim_words), 1)
        
        return overlap_ratio > 0.3  # 30% word overlap threshold
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            if self.search_client:
                stats = self.search_client.get_index_stats()
                return {
                    'total_documents': stats.get('document_count', 0),
                    'storage_size': stats.get('storage_size', 0),
                    'index_size': stats.get('index_size', 0),
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return {}
    
    async def search_knowledge_base(self, query: str, filters: Optional[str] = None) -> Dict[str, Any]:
        """Search the knowledge base with advanced filtering"""
        if not query or not query.strip():
            return {'error': 'Query cannot be empty'}
            
        try:
            if not self.search_client:
                return {'error': 'Search client not available'}
            
            # Generate query embedding
            query_embedding = await self.embedding_manager.generate_embeddings(query)
            
            # Perform search
            results = self.search_client.search_documents(
                query=query,
                vector_embedding=query_embedding,
                filters=filters,
                top=20,
                include_total_count=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return {'error': str(e)}
