"""
GuardianAI SDK Cost Calculator

Calculates token costs based on model pricing.
Implements Requirement 5.1 for accurate cost calculation.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing configuration for an LLM model."""
    model_name: str
    input_price_per_token: float
    output_price_per_token: float


# Pricing table for supported models
PRICING_TABLE: dict[str, ModelPricing] = {
    "gemini-pro": ModelPricing(
        model_name="gemini-pro",
        input_price_per_token=0.00025,   # $0.00025 per input token
        output_price_per_token=0.0005    # $0.0005 per output token
    ),
    "gemini-pro-vision": ModelPricing(
        model_name="gemini-pro-vision",
        input_price_per_token=0.00025,
        output_price_per_token=0.0005
    ),
    "gemini-ultra": ModelPricing(
        model_name="gemini-ultra",
        input_price_per_token=0.00125,   # Higher tier
        output_price_per_token=0.00375
    ),
    "gpt-4": ModelPricing(
        model_name="gpt-4",
        input_price_per_token=0.00003,
        output_price_per_token=0.00006
    ),
    "gpt-3.5-turbo": ModelPricing(
        model_name="gpt-3.5-turbo",
        input_price_per_token=0.0000015,
        output_price_per_token=0.000002
    ),
}

# Default pricing for unknown models
DEFAULT_PRICING = ModelPricing(
    model_name="default",
    input_price_per_token=0.00025,
    output_price_per_token=0.0005
)


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-pro"
) -> float:
    """
    Calculate the cost for an LLM request based on token usage.
    
    Implements Requirement 5.1:
    - Multiply input tokens by $0.00025
    - Multiply output tokens by $0.0005
    - For Gemini Pro pricing
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name for pricing lookup
    
    Returns:
        float: Total cost in USD
    
    Example:
        >>> cost = calculate_cost(1000, 500)
        >>> print(f"${cost:.4f}")
        $0.5000
    """
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts cannot be negative")
    
    pricing = PRICING_TABLE.get(model, DEFAULT_PRICING)
    
    input_cost = input_tokens * pricing.input_price_per_token
    output_cost = output_tokens * pricing.output_price_per_token
    
    return input_cost + output_cost


class CostCalculator:
    """
    Calculator for LLM token costs with model-specific pricing.
    
    Supports multiple models with configurable pricing.
    
    Example:
        >>> calc = CostCalculator(model="gemini-pro")
        >>> cost = calc.calculate(input_tokens=1000, output_tokens=500)
        >>> print(f"${cost:.4f}")
    """
    
    def __init__(self, model: str = "gemini-pro") -> None:
        """
        Initialize calculator with model pricing.
        
        Args:
            model: Model name for pricing lookup
        """
        self.model = model
        self.pricing = PRICING_TABLE.get(model, DEFAULT_PRICING)
    
    @property
    def input_price(self) -> float:
        """Get input token price."""
        return self.pricing.input_price_per_token
    
    @property
    def output_price(self) -> float:
        """Get output token price."""
        return self.pricing.output_price_per_token
    
    def calculate(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for given token counts.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            float: Total cost in USD
        """
        return calculate_cost(input_tokens, output_tokens, self.model)
    
    def calculate_from_text(
        self,
        input_text: str,
        output_text: str,
        chars_per_token: float = 4.0
    ) -> float:
        """
        Estimate cost from text by approximating token counts.
        
        Uses simple character-based estimation. For accurate counts,
        use the model's tokenizer.
        
        Args:
            input_text: Input text
            output_text: Output text
            chars_per_token: Average characters per token (default 4)
        
        Returns:
            float: Estimated cost in USD
        """
        input_tokens = int(len(input_text) / chars_per_token)
        output_tokens = int(len(output_text) / chars_per_token)
        
        return self.calculate(input_tokens, output_tokens)
    
    def estimate_daily_cost(
        self,
        avg_input_tokens: int,
        avg_output_tokens: int,
        requests_per_day: int
    ) -> float:
        """
        Estimate daily cost based on average usage.
        
        Args:
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            requests_per_day: Expected requests per day
        
        Returns:
            float: Estimated daily cost in USD
        """
        cost_per_request = self.calculate(avg_input_tokens, avg_output_tokens)
        return cost_per_request * requests_per_day
    
    def estimate_monthly_cost(
        self,
        avg_input_tokens: int,
        avg_output_tokens: int,
        requests_per_day: int
    ) -> float:
        """
        Estimate monthly cost (30 days) based on average usage.
        
        Args:
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            requests_per_day: Expected requests per day
        
        Returns:
            float: Estimated monthly cost in USD
        """
        return self.estimate_daily_cost(
            avg_input_tokens,
            avg_output_tokens,
            requests_per_day
        ) * 30
    
    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Get list of supported model names."""
        return list(PRICING_TABLE.keys())
    
    @classmethod
    def get_pricing(cls, model: str) -> Optional[ModelPricing]:
        """Get pricing for a specific model."""
        return PRICING_TABLE.get(model)
