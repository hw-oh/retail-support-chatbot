"""
Configuration for LLM-based shopping mall chatbot
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the chatbot"""
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MINI_MODEL: str = os.getenv("OPENAI_MINI_MODEL", "gpt-4o-mini")  # Smaller model for tools
    
    # Agent-specific models
    INTENT_AGENT_MODEL: str = os.getenv("INTENT_AGENT_MODEL", "gpt-4o")
    PLANNING_AGENT_MODEL: str = os.getenv("PLANNING_AGENT_MODEL", "gpt-4o-mini")
    ORDER_AGENT_MODEL: str = os.getenv("ORDER_AGENT_MODEL", "gpt-4o-mini")
    REFUND_AGENT_MODEL: str = os.getenv("REFUND_AGENT_MODEL", "gpt-4o")
    GENERAL_AGENT_MODEL: str = os.getenv("GENERAL_AGENT_MODEL", "gpt-4o-mini")
    
    # Scorer models
    POLICY_COMPLIANCE_MODEL: str = os.getenv("POLICY_COMPLIANCE_MODEL", "gpt-4o")
    REASON_QUALITY_MODEL: str = os.getenv("REASON_QUALITY_MODEL", "gpt-4o")
    REFUND_DECISION_MODEL: str = os.getenv("REFUND_DECISION_MODEL", "gpt-4o")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    
    # System Settings
    CURRENT_DATE: str = "2025-09-01"
    LANGUAGE: str = os.getenv("LANGUAGE", "ko")  # Default to Korean (ko, en, jp)
    
    # Prompt Settings
    USE_LOCAL_PROMPTS: bool = os.getenv("USE_LOCAL_PROMPTS", "1") == "1"  # 개발 시 로컬 프롬프트 사용
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            print("⚠️  Warning: OPENAI_API_KEY not set. Using mock mode.")
            return False
        return True


# Create config instance
config = Config()
