"""
General Response Agent
"""
import weave
from typing import List, Dict, Any
from .base import LLMClient
from prompts.agent_prompts import AGENT_PROMPTS


class GeneralAgent:
    """일반 응답 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """일반 문의 처리"""
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        system_prompt = AGENT_PROMPTS["general_agent"]["system"]
        user_prompt = f"""## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 현재 사용자 요청
{user_input}

## 작업 지시
위 대화 맥락을 고려하여 친근하고 도움이 되는 응답을 해주세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
