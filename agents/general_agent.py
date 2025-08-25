"""
General Response Agent
"""
import weave
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


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
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_general_agent_prompt()
        user_prompt = f"""
## 현재 사용자 입력: {user_input}

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 작업 지시
위 대화 맥락을 고려하여 친근하고 도움이 되는 응답을 해주세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
