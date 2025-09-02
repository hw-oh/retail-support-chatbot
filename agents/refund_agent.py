"""
Refund Management Agent
"""
import weave
import json
import re
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class RefundAgent:
    """환불 처리 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """환불 문의 처리"""
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # Weave에서 프롬프트 가져오기 (환불 정책은 이미 포함됨)
        system_prompt = prompt_manager.get_refund_agent_prompt()
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 작업 지시
위 대화 맥락을 고려하여 사용자의 환불 요청을 처리해주세요. 
응답은 다음 형식의 JSON으로 제공해주세요:

{{
    "refund_possible": true/false,
    "refund_fee": 숫자 (환불 수수료, 없으면 0),
    "total_refund_amount": 숫자 (실제 환불 금액),
    "reason": "환불 가능/불가능한 상세 이유",
    "user_response": "사용자에게 보여줄 친절한 응답",
    "policy_applied": ["적용된 정책 목록"]
}}

정확한 JSON 형식으로 응답해주세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages)
        
        # JSON 파싱 시도
        try:
            # JSON 코드 블록 제거
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif "```" in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            parsed_response = json.loads(response.strip())
            
            # 필수 필드 확인 및 기본값 설정
            result = {
                "refund_possible": parsed_response.get("refund_possible", False),
                "refund_fee": parsed_response.get("refund_fee", 0),
                "total_refund_amount": parsed_response.get("total_refund_amount", 0),
                "reason": parsed_response.get("reason", "환불 판단 정보 없음"),
                "user_response": parsed_response.get("user_response", response),
                "policy_applied": parsed_response.get("policy_applied", [])
            }
            
            # 자연스러운 대화체 응답 생성
            result["conversational_response"] = self._generate_conversational_response(result)
            
            return result
            
        except (json.JSONDecodeError, AttributeError) as e:
            # JSON 파싱 실패시 기본 응답 구조 반환
            return {
                "refund_possible": None,
                "refund_fee": 0,
                "total_refund_amount": 0,
                "reason": "JSON 파싱 실패",
                "user_response": response,
                "policy_applied": [],
                "conversational_response": response
            }
    
    def _safe_convert_to_number(self, value) -> float:
        """값을 안전하게 숫자로 변환"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                # 쉼표 제거 후 숫자 변환
                cleaned_value = value.replace(',', '').replace('원', '').strip()
                return float(cleaned_value)
            except (ValueError, AttributeError):
                return 0.0
        else:
            return 0.0
    
    def _generate_conversational_response(self, result: Dict[str, Any]) -> str:
        """구조화된 응답을 자연스러운 대화체로 변환"""
        refund_possible = result.get("refund_possible", False)
        refund_fee = self._safe_convert_to_number(result.get("refund_fee", 0))
        total_amount = self._safe_convert_to_number(result.get("total_refund_amount", 0))
        reason = result.get("reason", "")
        
        if refund_possible:
            # 환불 가능한 경우
            response = "네, 해당 주문에 대한 환불이 가능합니다! 😊\n\n"
            
            if refund_fee > 0:
                response += f"🔸 환불 수수료: {int(refund_fee):,}원\n"
                response += f"🔸 실제 환불 금액: {int(total_amount):,}원\n\n"
                response += "환불 시 수수료가 차감되어 처리됩니다. "
            else:
                response += f"🔸 환불 금액: {int(total_amount):,}원\n\n"
                response += "수수료 없이 전액 환불해드립니다! "
            
            response += "환불 처리를 원하시면 말씀해 주세요.\n\n"
            response += f"📝 환불 사유: {reason}"
            
        else:
            # 환불 불가능한 경우
            response = "죄송합니다. 해당 주문은 환불이 어려운 상황입니다. 😔\n\n"
            response += f"📝 사유: {reason}\n\n"
            response += "다른 도움이 필요하시면 언제든 말씀해 주세요!"
        
        return response