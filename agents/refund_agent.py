"""
Refund Management Agent
"""
import weave
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class RefundAgent:
    """환불 처리 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        
        # 환불 정책 로드
        with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
            self.refund_policy = f.read()
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """환불 문의 처리"""
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_refund_agent_prompt()
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 환불 정책
{self.refund_policy}

## 작업 지시
위 대화 맥락을 고려하여 사용자의 환불 요청을 처리해주세요. 
- 이전 대화에서 언급된 상품들이 있다면 그것을 기준으로 판단
- 각 상품별로 구체적인 환불 가능 여부와 이유를 설명
- 환불 정책을 정확히 적용하여 안내"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)