"""
Hallucination Detection and Prevention for AI Career Copilot
Implements multiple techniques to identify and prevent hallucinations in LLM responses.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class HallucinationCheck:
    """Represents a hallucination check result"""
    check_type: str
    passed: bool
    confidence: float
    details: Dict[str, Any]
    recommendations: List[str]

@dataclass
class HallucinationReport:
    """Comprehensive hallucination analysis report"""
    overall_risk: str  # 'low', 'medium', 'high'
    risk_score: float  # 0.0 to 1.0
    checks: List[HallucinationCheck]
    flagged_claims: List[str]
    source_attribution: Dict[str, List[str]]
    recommendations: List[str]
    metadata: Dict[str, Any]

class HallucinationDetector:
    """Detects potential hallucinations using multiple techniques"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        # Common hallucination patterns
        self.hallucination_patterns = [
            r'\b(always|never|everyone|nobody|everywhere|nowhere)\b',
            r'\b(guaranteed|100%|definitely|absolutely)\b',
            r'\b(proven|scientifically proven|research shows)\b',
            r'\b(according to studies|studies show|research indicates)\b',
            r'\b(experts agree|scientists say|doctors recommend)\b'
        ]
        
        # Confidence indicators
        self.confidence_indicators = [
            r'\b(maybe|perhaps|possibly|might|could)\b',
            r'\b(I think|I believe|in my opinion)\b',
            r'\b(according to|based on|as mentioned in)\b',
            r'\b(source:|reference:|cited from)\b'
        ]
    
    async def analyze_response(
        self, 
        response: str, 
        query: str, 
        sources: List[Dict[str, Any]] = None,
        context: str = None
    ) -> HallucinationReport:
        """Comprehensive hallucination analysis"""
        try:
            # Validate inputs
            if not response or not response.strip():
                raise ValueError("Response cannot be empty")
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            
            checks = []
            
            # 1. Pattern-based detection
            pattern_check = self._check_hallucination_patterns(response)
            checks.append(pattern_check)
            
            # 2. Source attribution check
            attribution_check = self._check_source_attribution(response, sources)
            checks.append(attribution_check)
            
            # 3. Context consistency check
            context_check = self._check_context_consistency(response, context)
            checks.append(context_check)
            
            # 4. Claim verification check
            claim_check = self._check_claim_verification(response, sources)
            checks.append(claim_check)
            
            # 5. Confidence level check
            confidence_check = self._check_confidence_level(response)
            checks.append(confidence_check)
            
            # 6. Specificity check
            specificity_check = self._check_specificity(response)
            checks.append(specificity_check)
            
            # Calculate overall risk
            risk_score = self._calculate_risk_score(checks)
            overall_risk = self._determine_risk_level(risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(checks, risk_score)
            
            # Extract flagged claims
            flagged_claims = self._extract_flagged_claims(response, checks)
            
            # Build source attribution mapping
            source_attribution = self._build_source_attribution(response, sources)
            
            return HallucinationReport(
                overall_risk=overall_risk,
                risk_score=risk_score,
                checks=checks,
                flagged_claims=flagged_claims,
                source_attribution=source_attribution,
                recommendations=recommendations,
                metadata={
                    'analyzed_at': datetime.now(timezone.utc).isoformat(),
                    'response_length': len(response),
                    'query_length': len(query),
                    'sources_count': len(sources) if sources else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing response for hallucinations: {e}")
            return self._create_error_report(str(e))
    
    def _check_hallucination_patterns(self, response: str) -> HallucinationCheck:
        """Check for common hallucination patterns"""
        if not response:
            return HallucinationCheck(
                check_type="pattern_detection",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        flagged_patterns = []
        pattern_count = 0
        
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                flagged_patterns.extend(matches)
                pattern_count += len(matches)
        
        # Calculate confidence based on pattern density
        confidence = max(0.0, 1.0 - (pattern_count * 0.1))
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Avoid absolute statements like 'always', 'never', 'everyone'",
                "Use qualifiers like 'may', 'might', 'could'",
                "Cite specific sources for claims",
                "Acknowledge uncertainty when appropriate"
            ])
        
        return HallucinationCheck(
            check_type="pattern_detection",
            passed=passed,
            confidence=confidence,
            details={
                'flagged_patterns': flagged_patterns,
                'pattern_count': pattern_count,
                'patterns_found': len(set(flagged_patterns))
            },
            recommendations=recommendations
        )
    
    def _check_source_attribution(self, response: str, sources: List[Dict[str, Any]] = None) -> HallucinationCheck:
        """Check if claims are properly attributed to sources"""
        if not response:
            return HallucinationCheck(
                check_type="source_attribution",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        if not sources:
            return HallucinationCheck(
                check_type="source_attribution",
                passed=False,
                confidence=0.0,
                details={'error': 'No sources provided'},
                recommendations=['Provide sources for verification']
            )
        
        # Look for attribution patterns
        attribution_patterns = [
            r'\b(according to|based on|as stated in|as mentioned in)\b',
            r'\b(source:|reference:|cited from|from)\b',
            r'\b(study|research|paper|article|report)\b'
        ]
        
        attribution_count = 0
        for pattern in attribution_patterns:
            attribution_count += len(re.findall(pattern, response, re.IGNORECASE))
        
        # Check if sources are actually referenced
        source_references = []
        for source in sources:
            source_id = source.get('id', 'unknown')
            if source_id in response or source.get('title', '') in response:
                source_references.append(source_id)
        
        # Calculate confidence
        attribution_score = min(1.0, attribution_count / max(len(sources), 1))
        source_score = len(source_references) / max(len(sources), 1)
        confidence = (attribution_score + source_score) / 2
        
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Cite specific sources for factual claims",
                "Use phrases like 'according to' or 'based on'",
                "Reference specific documents or studies",
                "Provide source URLs when available"
            ])
        
        return HallucinationCheck(
            check_type="source_attribution",
            passed=passed,
            confidence=confidence,
            details={
                'attribution_patterns_found': attribution_count,
                'sources_referenced': source_references,
                'total_sources': len(sources),
                'attribution_score': attribution_score,
                'source_score': source_score
            },
            recommendations=recommendations
        )
    
    def _check_context_consistency(self, response: str, context: str = None) -> HallucinationCheck:
        """Check if response is consistent with provided context"""
        if not response:
            return HallucinationCheck(
                check_type="context_consistency",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        if not context:
            return HallucinationCheck(
                check_type="context_consistency",
                passed=False,
                confidence=0.0,
                details={'error': 'No context provided'},
                recommendations=['Provide context for verification']
            )
        
        # Extract key terms from context and response
        context_terms = set(re.findall(r'\b\w{4,}\b', context.lower()))
        response_terms = set(re.findall(r'\b\w{4,}\b', response.lower()))
        
        # Calculate overlap
        overlap = len(context_terms.intersection(response_terms))
        total_unique = len(context_terms.union(response_terms))
        
        if total_unique == 0:
            confidence = 0.0
        else:
            confidence = overlap / total_unique
        
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Ensure response aligns with provided context",
                "Use terminology consistent with source material",
                "Avoid introducing concepts not in context",
                "Reference specific parts of the context"
            ])
        
        return HallucinationCheck(
            check_type="context_consistency",
            passed=passed,
            confidence=confidence,
            details={
                'context_terms': len(context_terms),
                'response_terms': len(response_terms),
                'overlap_terms': overlap,
                'total_unique_terms': total_unique,
                'consistency_ratio': confidence
            },
            recommendations=recommendations
        )
    
    def _check_claim_verification(self, response: str, sources: List[Dict[str, Any]] = None) -> HallucinationCheck:
        """Check if claims can be verified against sources"""
        if not response:
            return HallucinationCheck(
                check_type="claim_verification",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        if not sources:
            return HallucinationCheck(
                check_type="claim_verification",
                passed=False,
                confidence=0.0,
                details={'error': 'No sources provided'},
                recommendations=['Provide sources for verification']
            )
        
        # Extract factual claims
        claims = self._extract_factual_claims(response)
        
        verified_claims = 0
        unverified_claims = []
        
        for claim in claims:
            if self._can_verify_claim(claim, sources):
                verified_claims += 1
            else:
                unverified_claims.append(claim)
        
        confidence = verified_claims / max(len(claims), 1)
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Ensure all factual claims can be verified",
                "Provide specific evidence for claims",
                "Avoid making claims without supporting data",
                "Use qualifiers for uncertain information"
            ])
        
        return HallucinationCheck(
            check_type="claim_verification",
            passed=passed,
            confidence=confidence,
            details={
                'total_claims': len(claims),
                'verified_claims': verified_claims,
                'unverified_claims': unverified_claims,
                'verification_rate': confidence
            },
            recommendations=recommendations
        )
    
    def _check_confidence_level(self, response: str) -> HallucinationCheck:
        """Check if response uses appropriate confidence levels"""
        if not response:
            return HallucinationCheck(
                check_type="confidence_level",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        # Count confidence indicators
        confidence_indicators = 0
        for pattern in self.confidence_indicators:
            confidence_indicators += len(re.findall(pattern, response, re.IGNORECASE))
        
        # Count absolute statements
        absolute_statements = len(re.findall(r'\b(always|never|everyone|nobody|definitely|absolutely)\b', response, re.IGNORECASE))
        
        # Calculate confidence score
        if confidence_indicators == 0 and absolute_statements == 0:
            confidence = 0.5  # Neutral
        elif confidence_indicators > absolute_statements:
            confidence = 0.8  # Good
        elif absolute_statements > confidence_indicators:
            confidence = 0.2  # Poor
        else:
            confidence = 0.5  # Balanced
        
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Use confidence indicators like 'may', 'might', 'could'",
                "Avoid absolute statements",
                "Acknowledge uncertainty when appropriate",
                "Use qualifiers for speculative information"
            ])
        
        return HallucinationCheck(
            check_type="confidence_level",
            passed=passed,
            confidence=confidence,
            details={
                'confidence_indicators': confidence_indicators,
                'absolute_statements': absolute_statements,
                'confidence_balance': 'good' if confidence_indicators > absolute_statements else 'poor'
            },
            recommendations=recommendations
        )
    
    def _check_specificity(self, response: str) -> HallucinationCheck:
        """Check if response provides specific, actionable information"""
        if not response:
            return HallucinationCheck(
                check_type="specificity",
                passed=False,
                confidence=0.0,
                details={'error': 'Empty response'},
                recommendations=['Provide a response for analysis']
            )
            
        # Count specific details
        specific_patterns = [
            r'\b\d+\b',  # Numbers
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper nouns
            r'\b(https?://|www\.)\S+\b',  # URLs
            r'\b\d{4}\b',  # Years
            r'\b[A-Z]{2,}\b'  # Acronyms
        ]
        
        specificity_score = 0
        for pattern in specific_patterns:
            specificity_score += len(re.findall(pattern, response))
        
        # Normalize score
        normalized_score = min(1.0, specificity_score / 10)
        confidence = normalized_score
        passed = confidence >= self.confidence_threshold
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Provide specific numbers, dates, and names",
                "Include relevant URLs and references",
                "Use concrete examples and details",
                "Avoid vague generalizations"
            ])
        
        return HallucinationCheck(
            check_type="specificity",
            passed=passed,
            confidence=confidence,
            details={
                'specificity_score': specificity_score,
                'normalized_score': normalized_score,
                'specific_elements_found': specificity_score
            },
            recommendations=recommendations
        )
    
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract potential factual claims from text"""
        if not text:
            return []
            
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Look for sentences that make factual statements
            if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'had']):
                # Avoid questions and opinions
                if not sentence.endswith('?') and not any(word in sentence.lower() for word in ['think', 'believe', 'feel', 'opinion']):
                    claims.append(sentence)
        
        return claims[:10]  # Limit to 10 claims
    
    def _can_verify_claim(self, claim: str, sources: List[Dict[str, Any]]) -> bool:
        """Check if a claim can be verified against sources"""
        if not claim or not sources:
            return False
            
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        
        for source in sources:
            source_content = source.get('content', '')
            if not source_content:
                continue
            
            source_words = set(re.findall(r'\b\w+\b', source_content.lower()))
            
            # Calculate word overlap
            overlap = len(claim_words.intersection(source_words))
            overlap_ratio = overlap / max(len(claim_words), 1)
            
            if overlap_ratio > 0.3:  # 30% overlap threshold
                return True
        
        return False
    
    def _calculate_risk_score(self, checks: List[HallucinationCheck]) -> float:
        """Calculate overall hallucination risk score"""
        if not checks:
            return 1.0
        
        try:
            # Weight different checks
            weights = {
                'pattern_detection': 0.25,
                'source_attribution': 0.25,
                'context_consistency': 0.20,
                'claim_verification': 0.20,
                'confidence_level': 0.05,
                'specificity': 0.05
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for check in checks:
                weight = weights.get(check.check_type, 0.1)
                weighted_score += (1.0 - check.confidence) * weight
                total_weight += weight
            
            if total_weight == 0:
                return 1.0
            
            return weighted_score / total_weight
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score <= self.risk_thresholds['low']:
            return 'low'
        elif risk_score <= self.risk_thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    def _generate_recommendations(self, checks: List[HallucinationCheck], risk_score: float) -> List[str]:
        """Generate recommendations based on check results"""
        recommendations = []
        
        # Add specific recommendations from failed checks
        for check in checks:
            if not check.passed:
                recommendations.extend(check.recommendations)
        
        # Add general recommendations based on risk level
        if risk_score > 0.7:
            recommendations.extend([
                "Review all factual claims for accuracy",
                "Provide more source citations",
                "Use more conservative language",
                "Consider fact-checking workflow"
            ])
        elif risk_score > 0.4:
            recommendations.extend([
                "Improve source attribution",
                "Add confidence qualifiers",
                "Verify key claims against sources"
            ])
        else:
            recommendations.append("Continue current practices for maintaining accuracy")
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def _extract_flagged_claims(self, response: str, checks: List[HallucinationCheck]) -> List[str]:
        """Extract claims that were flagged by various checks"""
        if not response or not checks:
            return []
            
        flagged_claims = []
        
        for check in checks:
            if not check.passed:
                if check.check_type == 'pattern_detection':
                    # Extract sentences with flagged patterns
                    for pattern in self.hallucination_patterns:
                        matches = re.findall(pattern, response, re.IGNORECASE)
                        if matches:
                            # Find sentences containing these patterns
                            sentences = re.split(r'[.!?]+', response)
                            for sentence in sentences:
                                if any(match.lower() in sentence.lower() for match in matches):
                                    flagged_claims.append(sentence.strip())
        
        return list(set(flagged_claims))
    
    def _build_source_attribution(self, response: str, sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build mapping of claims to supporting sources"""
        if not response or not sources:
            return {}
            
        attribution = {}
        
        # Extract claims
        claims = self._extract_factual_claims(response)
        
        for claim in claims:
            supporting_sources = []
            claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
            
            for source in sources:
                source_content = source.get('content', '')
                if not source_content:
                    continue
                
                source_words = set(re.findall(r'\b\w+\b', source_content.lower()))
                overlap = len(claim_words.intersection(source_words))
                overlap_ratio = overlap / max(len(claim_words), 1)
                
                if overlap_ratio > 0.2:  # 20% overlap threshold
                    supporting_sources.append(source.get('id', 'unknown'))
            
            if supporting_sources:
                attribution[claim] = supporting_sources
        
        return attribution
    
    def _create_error_report(self, error_message: str) -> HallucinationReport:
        """Create an error report when analysis fails"""
        return HallucinationReport(
            overall_risk='unknown',
            risk_score=1.0,
            checks=[],
            flagged_claims=[],
            source_attribution={},
            recommendations=['Fix analysis error and retry'],
            metadata={'error': error_message}
        )
