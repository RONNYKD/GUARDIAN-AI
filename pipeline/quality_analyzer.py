"""
GuardianAI Quality Analyzer

Analyzes LLM response quality using various metrics.
Implements quality scoring for response relevance, coherence, and safety.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for an LLM response."""
    relevance_score: float  # How relevant to the prompt
    coherence_score: float  # How coherent/readable
    completeness_score: float  # How complete the answer
    safety_score: float  # How safe the content
    overall_score: float  # Combined score
    
    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "relevance_score": self.relevance_score,
            "coherence_score": self.coherence_score,
            "completeness_score": self.completeness_score,
            "safety_score": self.safety_score,
            "overall_score": self.overall_score,
        }


@dataclass
class QualityAnalysis:
    """Complete quality analysis result."""
    metrics: QualityMetrics
    passed: bool  # Whether quality meets threshold
    threshold: float
    issues: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": self.metrics.to_dict(),
            "passed": self.passed,
            "threshold": self.threshold,
            "issues": self.issues,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
        }


class QualityAnalyzer:
    """
    Analyzes LLM response quality.
    
    Uses heuristics to score:
    - Relevance: Does response address the prompt?
    - Coherence: Is response readable and well-structured?
    - Completeness: Does response fully answer?
    - Safety: Is response safe and appropriate?
    
    Example:
        >>> analyzer = QualityAnalyzer(quality_threshold=0.7)
        >>> analysis = analyzer.analyze(
        ...     prompt="What is Python?",
        ...     response="Python is a programming language..."
        ... )
        >>> print(f"Quality: {analysis.metrics.overall_score:.2f}")
    """
    
    # Quality threshold from requirements
    DEFAULT_QUALITY_THRESHOLD = 0.7
    
    def __init__(
        self,
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
        use_ai_scoring: bool = False,
    ) -> None:
        """
        Initialize quality analyzer.
        
        Args:
            quality_threshold: Minimum passing quality score
            use_ai_scoring: Whether to use AI for scoring (future)
        """
        self.quality_threshold = quality_threshold
        self.use_ai_scoring = use_ai_scoring
    
    def analyze(
        self,
        prompt: str,
        response: str,
        trace_id: Optional[str] = None,
    ) -> QualityAnalysis:
        """
        Analyze response quality.
        
        Args:
            prompt: The user prompt
            response: The LLM response
            trace_id: Trace ID for correlation
        
        Returns:
            QualityAnalysis with metrics and pass/fail
        """
        issues = []
        
        # Calculate individual scores
        relevance = self._score_relevance(prompt, response)
        coherence = self._score_coherence(response)
        completeness = self._score_completeness(prompt, response)
        safety = self._score_safety(response)
        
        # Check for issues
        if relevance < 0.5:
            issues.append("Low relevance to prompt")
        if coherence < 0.5:
            issues.append("Poor coherence/readability")
        if completeness < 0.5:
            issues.append("Incomplete response")
        if safety < 0.7:
            issues.append("Potential safety concerns")
        
        # Calculate overall score (weighted average)
        overall = (
            relevance * 0.3 +
            coherence * 0.25 +
            completeness * 0.25 +
            safety * 0.2
        )
        
        metrics = QualityMetrics(
            relevance_score=relevance,
            coherence_score=coherence,
            completeness_score=completeness,
            safety_score=safety,
            overall_score=overall,
        )
        
        passed = overall >= self.quality_threshold
        
        return QualityAnalysis(
            metrics=metrics,
            passed=passed,
            threshold=self.quality_threshold,
            issues=issues,
            trace_id=trace_id,
        )
    
    def _score_relevance(self, prompt: str, response: str) -> float:
        """
        Score how relevant response is to prompt.
        
        Uses keyword overlap and semantic indicators.
        """
        if not response or not prompt:
            return 0.0
        
        # Extract significant words from prompt
        prompt_words = set(self._extract_keywords(prompt.lower()))
        response_words = set(self._extract_keywords(response.lower()))
        
        if not prompt_words:
            return 0.8  # Default if no keywords extracted
        
        # Calculate overlap
        overlap = prompt_words.intersection(response_words)
        overlap_ratio = len(overlap) / len(prompt_words)
        
        # Check for question-answer indicators
        if self._is_question(prompt) and self._has_answer_structure(response):
            overlap_ratio = min(overlap_ratio + 0.2, 1.0)
        
        # Minimum relevance if response is substantive
        if len(response) > 50 and overlap_ratio < 0.3:
            overlap_ratio = 0.3
        
        return min(max(overlap_ratio, 0.0), 1.0)
    
    def _score_coherence(self, response: str) -> float:
        """
        Score response coherence and readability.
        
        Checks sentence structure, punctuation, formatting.
        """
        if not response:
            return 0.0
        
        score = 1.0
        
        # Check for proper sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.3
        
        # Average sentence length (too short or too long is bad)
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_length < 3:
            score -= 0.3
        elif avg_length > 50:
            score -= 0.2
        
        # Check for capitalization
        properly_capitalized = sum(
            1 for s in sentences if s and s[0].isupper()
        )
        cap_ratio = properly_capitalized / len(sentences)
        if cap_ratio < 0.5:
            score -= 0.2
        
        # Check for excessive repetition
        words = response.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # Too repetitive
                score -= 0.3
        
        # Check for code blocks if technical
        if "```" in response:
            score = min(score + 0.1, 1.0)  # Bonus for code formatting
        
        return max(score, 0.0)
    
    def _score_completeness(self, prompt: str, response: str) -> float:
        """
        Score response completeness.
        
        Checks if response adequately addresses the prompt.
        """
        if not response:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length relative to prompt complexity
        prompt_complexity = len(prompt.split())
        response_length = len(response.split())
        
        # Expect some minimum response
        if response_length < 5:
            score = 0.2
        elif response_length >= prompt_complexity:
            score = 0.7
        
        # Check for list/enumeration when multiple questions
        if self._count_questions(prompt) > 1:
            if any(marker in response for marker in ["1.", "2.", "-", "•", "first", "second"]):
                score = min(score + 0.2, 1.0)
        
        # Check for conclusion/summary indicators
        conclusion_indicators = [
            "in summary", "in conclusion", "therefore",
            "to summarize", "overall", "in short"
        ]
        if any(ind in response.lower() for ind in conclusion_indicators):
            score = min(score + 0.1, 1.0)
        
        # Check for incomplete sentences at end
        if response.rstrip()[-1:] not in ".!?\"'":
            score -= 0.2
        
        return max(score, 0.0)
    
    def _score_safety(self, response: str) -> float:
        """
        Score response safety.
        
        Checks for potentially harmful content.
        """
        if not response:
            return 1.0
        
        score = 1.0
        response_lower = response.lower()
        
        # Warning phrases that reduce safety score
        warning_phrases = [
            "i cannot", "i can't", "i won't",
            "not appropriate", "harmful", "dangerous",
            "illegal", "unethical"
        ]
        
        for phrase in warning_phrases:
            if phrase in response_lower:
                # Actually indicates good safety - model is refusing
                score = min(score + 0.1, 1.0)
                break
        
        # Check for potential harmful patterns
        harmful_patterns = [
            r"how to (?:hack|steal|kill|harm)",
            r"instructions for (?:weapon|bomb|drug)",
            r"personal information.*\d{3}[-\s]?\d{2}[-\s]?\d{4}",  # SSN
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, response_lower):
                score -= 0.4
        
        return max(score, 0.0)
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract significant keywords from text."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all", "each",
            "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very",
            "just", "and", "but", "if", "or", "because", "until", "while",
            "this", "that", "these", "those", "what", "which", "who",
            "i", "me", "my", "you", "your", "he", "she", "it", "we", "they",
        }
        
        words = re.findall(r'\b[a-z]+\b', text)
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a question."""
        return "?" in text or text.lower().startswith((
            "what", "who", "where", "when", "why", "how",
            "can", "could", "would", "should", "is", "are",
            "do", "does", "did"
        ))
    
    def _has_answer_structure(self, text: str) -> bool:
        """Check if text has answer-like structure."""
        indicators = [
            "is", "are", "was", "were",
            "means", "refers to", "defined as",
            "because", "due to", "since",
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)
    
    def _count_questions(self, text: str) -> int:
        """Count number of questions in text."""
        return text.count("?")


def analyze_quality(
    prompt: str,
    response: str,
    threshold: float = 0.7,
    trace_id: Optional[str] = None,
) -> QualityAnalysis:
    """
    Convenience function for quality analysis.
    
    Args:
        prompt: The user prompt
        response: The LLM response
        threshold: Quality threshold
        trace_id: Trace ID
    
    Returns:
        QualityAnalysis result
    """
    analyzer = QualityAnalyzer(quality_threshold=threshold)
    return analyzer.analyze(prompt, response, trace_id)
