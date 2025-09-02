"""
Order Management Agent
"""
import weave
import json
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class OrderAgent:
    """주문 조회 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        
        # 데이터 로드
        with open('data/purchase_history.json', 'r', encoding='utf-8') as f:
            self.purchase_data = json.load(f)
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """주문 조회 처리"""
        
        # 주문 데이터 검색 로직
        orders = self.purchase_data if isinstance(self.purchase_data, list) else self.purchase_data.get('orders', [])
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_order_agent_prompt()
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 주문 데이터
{json.dumps(orders[:10], ensure_ascii=False, indent=2)}

## 작업 지시
위 대화 맥락을 고려하여 사용자 요청에 맞는 주문 정보를 찾아서 친절하게 안내해주세요.
- 이전 대화에서 언급된 조건이나 필터가 있다면 적용
- 사용자가 참조하는 이전 정보가 있다면 연결하여 설명
- 환불 등 액션이 필요한 정보는 설명하지 말 것."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
