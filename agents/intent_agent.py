"""
Intent Classification Agent
"""
import weave
import json
from typing import List, Dict, Any
from datetime import datetime
from .base import LLMClient
from prompts.intent_prompts import INTENT_PROMPTS


class IntentAgent:
    """의도 분석 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    @weave.op()
    def classify(self, user_input: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """사용자 입력의 의도 분류"""
        
        # 대화 히스토리 준비
        history_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴만
            for turn in recent_turns:
                history_text += f"사용자: {turn.get('user', '')}\n봇: {turn.get('bot', '')}\n"
        
        # 프롬프트 준비
        system_prompt = INTENT_PROMPTS["ko"]["system"].format(
            current_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        user_prompt = f"""## 분석할 입력

**대화 히스토리:**
{history_text if history_text.strip() else "(첫 대화)"}

**현재 사용자 입력:** "{user_input}"

## 작업
위 사용자 입력을 분석하여 의도를 분류하고 엔티티를 추출하세요.

**출력 형식 (JSON만):**
{{
    "intent": "분류된_의도",
    "confidence": 0.95,
    "entities": {{
        "order_id": "ORD번호_또는_null",
        "product_name": "상품명_또는_null", 
        "time_reference": "시간표현_또는_null",
        "quantity": 숫자_또는_null,
        "refund_reason": "사유_또는_null",
        "refund_reference": true_또는_false,
        "selection_type": "선택유형_또는_null"
    }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.3)
        
        try:
            # JSON 마크다운 블록 제거
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"[DEBUG] JSON 파싱 실패: {e}")
            print(f"[DEBUG] 원본 응답: {repr(response)}")
            # JSON 파싱 실패시 기본값
            return {
                "intent": "general_chat",
                "confidence": 0.5,
                "entities": {}
            }
