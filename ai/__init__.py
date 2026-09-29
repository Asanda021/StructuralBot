"""
StructuralBot - AI Package

AI services for:
- Engineering assistance
- Calculation explanation
- Result review
- Project analysis
- Report assistance

The Telegram handler must not contain provider-specific AI logic.
Provider integrations will be added under this package.
"""

from ai.service import (
    AIError,
    AIConfigurationError,
    AIProviderError,
    AIResponse,
    AIRequest,
    AIService,
    get_ai_service,
)

__all__ = [
    "AIError",
    "AIConfigurationError",
    "AIProviderError",
    "AIResponse",
    "AIRequest",
    "AIService",
    "get_ai_service",
]
