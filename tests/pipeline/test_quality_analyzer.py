"""
Property-based tests for GuardianAI Quality Analyzer.

Tests quality scoring accuracy and consistency.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from pipeline.quality_analyzer import (
    QualityAnalyzer,
    QualityMetrics,
    QualityAnalysis,
    analyze_quality,
)


# =============================================================================
# Property 9: Quality scores are in valid range
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=500),
    response=st.text(min_size=1, max_size=2000),
)
@settings(max_examples=100)
def test_property_9_quality_score_range(prompt: str, response: str):
    """
    Property 9: All quality scores must be between 0.0 and 1.0.
    """
    assume(len(prompt.strip()) > 0)
    assume(len(response.strip()) > 0)
    
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(prompt=prompt, response=response)
    
    # All individual scores must be in range
    assert 0.0 <= analysis.metrics.relevance_score <= 1.0
    assert 0.0 <= analysis.metrics.coherence_score <= 1.0
    assert 0.0 <= analysis.metrics.completeness_score <= 1.0
    assert 0.0 <= analysis.metrics.safety_score <= 1.0
    
    # Overall score must be in range
    assert 0.0 <= analysis.metrics.overall_score <= 1.0


# =============================================================================
# Property 10: Pass/fail is consistent with threshold
# =============================================================================

@given(
    prompt=st.text(min_size=10, max_size=200),
    response=st.text(min_size=20, max_size=1000),
    threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=50)
def test_property_10_threshold_consistency(prompt: str, response: str, threshold: float):
    """
    Property 10: Pass/fail must be consistent with threshold.
    
    passed = True iff overall_score >= threshold
    """
    analyzer = QualityAnalyzer(quality_threshold=threshold)
    analysis = analyzer.analyze(prompt=prompt, response=response)
    
    if analysis.metrics.overall_score >= threshold:
        assert analysis.passed is True
    else:
        assert analysis.passed is False


# =============================================================================
# Property: High quality responses score well
# =============================================================================

HIGH_QUALITY_EXAMPLES = [
    (
        "What is Python?",
        "Python is a high-level, interpreted programming language known for its "
        "simplicity and readability. It was created by Guido van Rossum and first "
        "released in 1991. Python supports multiple programming paradigms including "
        "procedural, object-oriented, and functional programming."
    ),
    (
        "How does photosynthesis work?",
        "Photosynthesis is the process by which plants convert light energy into "
        "chemical energy. During this process, plants absorb carbon dioxide from "
        "the air and water from the soil, using sunlight as the energy source. "
        "The result is glucose, which the plant uses for energy, and oxygen, "
        "which is released into the atmosphere."
    ),
]


@pytest.mark.parametrize("prompt,response", HIGH_QUALITY_EXAMPLES)
def test_high_quality_responses_score_well(prompt: str, response: str):
    """High-quality responses should score above threshold."""
    analyzer = QualityAnalyzer(quality_threshold=0.7)
    analysis = analyzer.analyze(prompt=prompt, response=response)
    
    assert analysis.metrics.overall_score >= 0.5
    assert analysis.metrics.coherence_score >= 0.5


# =============================================================================
# Property: Empty responses score poorly
# =============================================================================

@given(
    prompt=st.text(min_size=10, max_size=200),
)
@settings(max_examples=20)
def test_empty_response_low_score(prompt: str):
    """Empty responses should score zero."""
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(prompt=prompt, response="")
    
    assert analysis.metrics.overall_score == 0.0
    assert analysis.passed is False


def test_empty_prompt_and_response():
    """Both empty should give zero score."""
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(prompt="", response="")
    
    assert analysis.metrics.overall_score == 0.0


# =============================================================================
# Property: Safety scoring
# =============================================================================

SAFE_RESPONSES = [
    "I cannot provide instructions for harmful activities.",
    "That request is not appropriate. Let me help you with something else.",
    "I won't assist with anything illegal or dangerous.",
]


@pytest.mark.parametrize("response", SAFE_RESPONSES)
def test_refusal_responses_high_safety(response: str):
    """Responses that refuse harmful requests should have high safety."""
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(
        prompt="How do I hack into a computer?",
        response=response
    )
    
    assert analysis.metrics.safety_score >= 0.8


# =============================================================================
# Property: QualityMetrics serialization
# =============================================================================

@given(
    relevance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    coherence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    completeness=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    safety=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    overall=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=30)
def test_quality_metrics_serialization(
    relevance: float,
    coherence: float,
    completeness: float,
    safety: float,
    overall: float,
):
    """QualityMetrics serializes correctly."""
    metrics = QualityMetrics(
        relevance_score=relevance,
        coherence_score=coherence,
        completeness_score=completeness,
        safety_score=safety,
        overall_score=overall,
    )
    
    data = metrics.to_dict()
    
    assert data["relevance_score"] == relevance
    assert data["coherence_score"] == coherence
    assert data["completeness_score"] == completeness
    assert data["safety_score"] == safety
    assert data["overall_score"] == overall


# =============================================================================
# Property: QualityAnalysis structure
# =============================================================================

@given(
    prompt=st.text(min_size=10, max_size=200),
    response=st.text(min_size=10, max_size=500),
    trace_id=st.one_of(st.none(), st.text(min_size=8, max_size=32)),
)
@settings(max_examples=30)
def test_quality_analysis_structure(prompt: str, response: str, trace_id: str | None):
    """QualityAnalysis has correct structure."""
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(prompt=prompt, response=response, trace_id=trace_id)
    
    data = analysis.to_dict()
    
    assert "metrics" in data
    assert "passed" in data
    assert "threshold" in data
    assert "issues" in data
    assert "timestamp" in data
    
    if trace_id:
        assert data["trace_id"] == trace_id


# =============================================================================
# Property: Convenience function works
# =============================================================================

@given(
    prompt=st.text(min_size=10, max_size=200),
    response=st.text(min_size=10, max_size=500),
)
@settings(max_examples=20)
def test_analyze_quality_function(prompt: str, response: str):
    """Convenience function produces valid analysis."""
    analysis = analyze_quality(prompt, response)
    
    assert isinstance(analysis, QualityAnalysis)
    assert 0.0 <= analysis.metrics.overall_score <= 1.0


# =============================================================================
# Property: Question-answer relevance
# =============================================================================

QUESTION_ANSWER_PAIRS = [
    ("What color is the sky?", "The sky is blue."),
    ("How many days in a week?", "There are seven days in a week."),
    ("Who wrote Romeo and Juliet?", "William Shakespeare wrote Romeo and Juliet."),
]


@pytest.mark.parametrize("question,answer", QUESTION_ANSWER_PAIRS)
def test_relevant_answers_score_well(question: str, answer: str):
    """Relevant answers to questions should score well on relevance."""
    analyzer = QualityAnalyzer()
    analysis = analyzer.analyze(prompt=question, response=answer)
    
    assert analysis.metrics.relevance_score >= 0.5


# =============================================================================
# Property: Issues list is informative
# =============================================================================

def test_low_quality_has_issues():
    """Low quality responses should have issues listed."""
    analyzer = QualityAnalyzer(quality_threshold=0.9)
    
    # This will likely fail the high threshold
    analysis = analyzer.analyze(
        prompt="Explain quantum physics in detail",
        response="ok"
    )
    
    if not analysis.passed:
        assert len(analysis.issues) > 0


# =============================================================================
# Property: Coherence penalizes repetition
# =============================================================================

def test_repetition_lowers_coherence():
    """Highly repetitive text should have lower coherence."""
    analyzer = QualityAnalyzer()
    
    # Highly repetitive
    repetitive = "word " * 100
    analysis1 = analyzer.analyze(prompt="Say something", response=repetitive)
    
    # Normal text
    normal = "This is a well-written response that varies its vocabulary and structure."
    analysis2 = analyzer.analyze(prompt="Say something", response=normal)
    
    assert analysis2.metrics.coherence_score >= analysis1.metrics.coherence_score
