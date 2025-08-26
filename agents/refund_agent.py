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
        
        # 환불 정책 로드
        with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
            self.refund_policy = f.read()
    
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
            
            return result
            
        except (json.JSONDecodeError, AttributeError) as e:
            # JSON 파싱 실패시 기본 응답 구조 반환
            return {
                "refund_possible": None,
                "refund_fee": 0,
                "total_refund_amount": 0,
                "reason": "JSON 파싱 실패",
                "user_response": response,
                "policy_applied": []
            }