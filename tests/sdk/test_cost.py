"""
Property-based tests for GuardianAI SDK Cost Calculator.

Tests Requirement 5.1 for cost calculation accuracy.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math

from guardianai.cost import (
    calculate_cost,
    CostCalculator,
    ModelPricing,
    PRICING_TABLE,
    DEFAULT_PRICING,
)


# =============================================================================
# Property 17: Cost calculation accuracy (Requirement 5.1)
# =============================================================================

@given(
    input_tokens=st.integers(min_value=0, max_value=10000000),
    output_tokens=st.integers(min_value=0, max_value=10000000),
)
@settings(max_examples=200)
def test_property_17_cost_calculation_gemini_pro(input_tokens: int, output_tokens: int):
    """
    Property 17: Cost calculation must match pricing formula.
    
    Requirement 5.1: For Gemini Pro:
    - Input: $0.00025 per token
    - Output: $0.0005 per token
    - Cost = (input_tokens * 0.00025) + (output_tokens * 0.0005)
    """
    cost = calculate_cost(input_tokens, output_tokens, model="gemini-pro")
    
    # Calculate expected cost per Requirement 5.1
    expected_input_cost = input_tokens * 0.00025
    expected_output_cost = output_tokens * 0.0005
    expected_total = expected_input_cost + expected_output_cost
    
    # Allow small floating point tolerance
    assert math.isclose(cost, expected_total, rel_tol=1e-9), \
        f"Cost {cost} != expected {expected_total}"
    
    # Cost must be non-negative
    assert cost >= 0, "Cost cannot be negative"


@given(
    input_tokens=st.integers(min_value=0, max_value=1000000),
    output_tokens=st.integers(min_value=0, max_value=1000000),
    model=st.sampled_from(list(PRICING_TABLE.keys())),
)
@settings(max_examples=100)
def test_cost_calculation_all_models(input_tokens: int, output_tokens: int, model: str):
    """Cost calculation works for all supported models."""
    cost = calculate_cost(input_tokens, output_tokens, model)
    
    pricing = PRICING_TABLE[model]
    expected = (
        input_tokens * pricing.input_price_per_token +
        output_tokens * pricing.output_price_per_token
    )
    
    assert math.isclose(cost, expected, rel_tol=1e-9)
    assert cost >= 0


# =============================================================================
# Property: Cost scales linearly with tokens
# =============================================================================

@given(
    base_input=st.integers(min_value=0, max_value=100000),
    base_output=st.integers(min_value=0, max_value=100000),
    multiplier=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_cost_linear_scaling(base_input: int, base_output: int, multiplier: int):
    """Cost scales linearly with token count."""
    base_cost = calculate_cost(base_input, base_output)
    scaled_cost = calculate_cost(base_input * multiplier, base_output * multiplier)
    
    expected_scaled = base_cost * multiplier
    
    assert math.isclose(scaled_cost, expected_scaled, rel_tol=1e-9)


# =============================================================================
# Property: Cost is additive
# =============================================================================

@given(
    input1=st.integers(min_value=0, max_value=100000),
    input2=st.integers(min_value=0, max_value=100000),
    output1=st.integers(min_value=0, max_value=100000),
    output2=st.integers(min_value=0, max_value=100000),
)
@settings(max_examples=100)
def test_cost_additivity(input1: int, input2: int, output1: int, output2: int):
    """Cost of combined tokens equals sum of individual costs."""
    cost1 = calculate_cost(input1, output1)
    cost2 = calculate_cost(input2, output2)
    combined_cost = calculate_cost(input1 + input2, output1 + output2)
    
    assert math.isclose(combined_cost, cost1 + cost2, rel_tol=1e-9)


# =============================================================================
# Property: Zero tokens = zero cost
# =============================================================================

def test_zero_tokens_zero_cost():
    """Zero tokens always results in zero cost."""
    for model in PRICING_TABLE.keys():
        cost = calculate_cost(0, 0, model)
        assert cost == 0.0


# =============================================================================
# Property: Output tokens cost more than input for Gemini
# =============================================================================

@given(
    tokens=st.integers(min_value=1, max_value=1000000),
)
@settings(max_examples=50)
def test_output_costs_more_than_input_gemini(tokens: int):
    """For Gemini Pro, output tokens cost more than input tokens."""
    input_only_cost = calculate_cost(tokens, 0, "gemini-pro")
    output_only_cost = calculate_cost(0, tokens, "gemini-pro")
    
    # Per pricing: output = $0.0005, input = $0.00025
    # So output should be 2x input
    assert output_only_cost > input_only_cost
    assert math.isclose(output_only_cost / input_only_cost, 2.0, rel_tol=1e-9)


# =============================================================================
# Property: CostCalculator class methods
# =============================================================================

@given(
    input_tokens=st.integers(min_value=0, max_value=1000000),
    output_tokens=st.integers(min_value=0, max_value=1000000),
)
@settings(max_examples=50)
def test_cost_calculator_class(input_tokens: int, output_tokens: int):
    """CostCalculator class produces same results as function."""
    calc = CostCalculator(model="gemini-pro")
    
    class_result = calc.calculate(input_tokens, output_tokens)
    func_result = calculate_cost(input_tokens, output_tokens, "gemini-pro")
    
    assert class_result == func_result


@given(
    input_text=st.text(max_size=10000),
    output_text=st.text(max_size=10000),
)
@settings(max_examples=50)
def test_cost_from_text_estimation(input_text: str, output_text: str):
    """Text-based cost estimation is reasonable."""
    calc = CostCalculator(model="gemini-pro")
    
    cost = calc.calculate_from_text(input_text, output_text)
    
    # Cost should be non-negative
    assert cost >= 0
    
    # Empty text should have zero cost
    if len(input_text) < 4 and len(output_text) < 4:
        assert cost == 0


# =============================================================================
# Property: Daily/monthly cost estimation
# =============================================================================

@given(
    avg_input=st.integers(min_value=0, max_value=10000),
    avg_output=st.integers(min_value=0, max_value=10000),
    requests_per_day=st.integers(min_value=0, max_value=100000),
)
@settings(max_examples=50)
def test_daily_monthly_cost_estimation(
    avg_input: int,
    avg_output: int,
    requests_per_day: int,
):
    """Daily and monthly cost estimations are consistent."""
    calc = CostCalculator(model="gemini-pro")
    
    daily = calc.estimate_daily_cost(avg_input, avg_output, requests_per_day)
    monthly = calc.estimate_monthly_cost(avg_input, avg_output, requests_per_day)
    
    # Monthly should be 30x daily
    assert math.isclose(monthly, daily * 30, rel_tol=1e-9)
    
    # Both should be non-negative
    assert daily >= 0
    assert monthly >= 0


# =============================================================================
# Property: Negative tokens raise error
# =============================================================================

@given(
    input_tokens=st.integers(max_value=-1),
    output_tokens=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20)
def test_negative_input_tokens_raises(input_tokens: int, output_tokens: int):
    """Negative input tokens must raise ValueError."""
    with pytest.raises(ValueError, match="negative"):
        calculate_cost(input_tokens, output_tokens)


@given(
    input_tokens=st.integers(min_value=0, max_value=1000),
    output_tokens=st.integers(max_value=-1),
)
@settings(max_examples=20)
def test_negative_output_tokens_raises(input_tokens: int, output_tokens: int):
    """Negative output tokens must raise ValueError."""
    with pytest.raises(ValueError, match="negative"):
        calculate_cost(input_tokens, output_tokens)


# =============================================================================
# Property: Unknown model uses default pricing
# =============================================================================

@given(
    unknown_model=st.text(min_size=1, max_size=32).filter(
        lambda x: x not in PRICING_TABLE
    ),
    input_tokens=st.integers(min_value=0, max_value=10000),
    output_tokens=st.integers(min_value=0, max_value=10000),
)
@settings(max_examples=30)
def test_unknown_model_uses_default(
    unknown_model: str,
    input_tokens: int,
    output_tokens: int,
):
    """Unknown models fall back to default pricing."""
    cost = calculate_cost(input_tokens, output_tokens, unknown_model)
    
    expected = (
        input_tokens * DEFAULT_PRICING.input_price_per_token +
        output_tokens * DEFAULT_PRICING.output_price_per_token
    )
    
    assert math.isclose(cost, expected, rel_tol=1e-9)
