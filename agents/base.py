"""
Base LLM Client
"""
from typing import List, Dict
from config import config


class LLMClient:
    """간단한 LLM 클라이언트"""
    
    def __init__(self, model: str = "gpt-4o"):
        import openai
        self.client = openai.OpenAI(
            api_key=config.OPENAI_API_KEY
            # 표준 OpenAI API 사용 (base_url 제거)
        )
        self.model = model
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """채팅 완성 요청"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM 호출 오류: {str(e)}"