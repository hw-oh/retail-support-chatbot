"""
Base LLM client and utilities
"""
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import json
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed
from config import config


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages"""
        pass
    
    @abstractmethod
    def generate_json(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate JSON response with schema validation"""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.temperature = config.TEMPERATURE
        self.max_tokens = config.MAX_TOKENS
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            
    @retry(stop=stop_after_attempt(config.MAX_RETRIES), wait=wait_fixed(config.RETRY_DELAY))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate text response"""
        if not self.client:
            # Mock response for testing without API key
            return self._mock_generate(messages)
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        
        return response.choices[0].message.content
    
    @retry(stop=stop_after_attempt(config.MAX_RETRIES), wait=wait_fixed(config.RETRY_DELAY))
    def generate_json(self, messages: List[Dict[str, str]], schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Generate JSON response"""
        if not self.client:
            # Mock response for testing without API key
            return self._mock_generate_json(messages, schema)
            
        # Add JSON instruction to the last message
        json_instruction = "\n\nPlease respond with valid JSON that matches the required schema."
        if schema:
            json_instruction += f"\n\nSchema: {json.dumps(schema, indent=2)}"
            
        messages_copy = messages.copy()
        messages_copy[-1]["content"] += json_instruction
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages_copy,
            temperature=kwargs.get("temperature", 0.3),  # Lower temperature for structured output
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse JSON from response: {content}")
    
    def _mock_generate(self, messages: List[Dict[str, str]]) -> str:
        """Mock text generation for testing"""
        last_message = messages[-1]["content"]
        
        # Simple rule-based responses for testing
        if "환불" in last_message:
            return "환불 처리를 도와드리겠습니다. 주문번호를 알려주시겠어요?"
        elif "주문" in last_message:
            return "주문 내역을 확인해드리겠습니다."
        elif "제품" in last_message or "상품" in last_message:
            return "제품 정보를 찾아드리겠습니다."
        else:
            return "무엇을 도와드릴까요?"
    
    def _mock_generate_json(self, messages: List[Dict[str, str]], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock JSON generation for testing"""
        last_message = messages[-1]["content"]
        
        # Simple intent classification
        if "환불" in last_message:
            return {"intent": "refund_inquiry", "confidence": 0.9}
        elif "주문" in last_message:
            return {"intent": "order_status", "confidence": 0.85}
        elif "제품" in last_message:
            return {"intent": "product_inquiry", "confidence": 0.8}
        else:
            return {"intent": "general_chat", "confidence": 0.5}


class MockLLMClient(LLMClient):
    """Mock LLM client for testing"""
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Mock text generation"""
        return "This is a mock response for testing."
    
    def generate_json(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock JSON generation"""
        return {"mock": True, "message": "This is a mock JSON response"}


def get_llm_client(use_mock: bool = False) -> LLMClient:
    """Factory function to get LLM client"""
    if use_mock or not config.OPENAI_API_KEY:
        return MockLLMClient()
    return OpenAIClient()
