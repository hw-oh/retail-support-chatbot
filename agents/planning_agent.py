"""
Planning Agent
"""
import weave
import json
import re
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class PlanningAgent:
    """작업 계획 수립 에이전트"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    @weave.op()
    def create_plan(self, user_input: str, intent_result: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        사용자 의도에 따른 작업 계획 수립
        
        Args:
            user_input: 사용자 입력
            intent_result: Intent Agent 결과
            context: 대화 맥락
            
        Returns:
            계획 정보 (실행할 에이전트들의 순서와 파라미터)
        """
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # Planning 시스템 프롬프트
        system_prompt = self._get_planning_prompt()
        
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

**Intent 분석 결과:**
- 의도: {intent_result.get('intent', 'unknown')}
- 신뢰도: {intent_result.get('confidence', 0.0)}
- 엔티티: {json.dumps(intent_result.get('entities', {}), ensure_ascii=False)}

**대화 맥락:**
{context_text if context_text.strip() else "(첫 대화)"}

## 작업
위 정보를 바탕으로 사용자 요청을 완전히 처리하기 위한 단계별 실행 계획을 수립하세요.

**출력 형식 (JSON만):**
{{
    "plan_type": "single_agent|multi_step",
    "reason": "계획 수립 이유",
    "steps": [
        {{
            "step_id": 1,
            "agent": "order_agent|refund_agent|general_agent",
            "purpose": "이 단계의 목적",
            "parameters": {{
                "search_product": "제품명_또는_null",
                "order_id": "주문번호_또는_null", 
                "context_from_previous": true_또는_false
            }}
        }}
    ],
    "expected_outcome": "기대되는 최종 결과"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.2)
        
        try:
            # JSON 파싱
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif "```" in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            plan = json.loads(response.strip())
            
            # 필수 필드 검증 및 기본값 설정
            validated_plan = {
                "plan_type": plan.get("plan_type", "single_agent"),
                "reason": plan.get("reason", "기본 처리"),
                "steps": plan.get("steps", []),
                "expected_outcome": plan.get("expected_outcome", "사용자 요청 처리")
            }
            
            # 단계별 검증
            for i, step in enumerate(validated_plan["steps"]):
                if "agent" not in step:
                    validated_plan["steps"][i]["agent"] = "general_agent"
                if "purpose" not in step:
                    validated_plan["steps"][i]["purpose"] = "일반 처리"
                if "parameters" not in step:
                    validated_plan["steps"][i]["parameters"] = {}
                if "step_id" not in step:
                    validated_plan["steps"][i]["step_id"] = i + 1
            
            return validated_plan
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[DEBUG] Planning Agent JSON 파싱 실패: {e}")
            # 파싱 실패시 기본 계획 반환
            return self._create_fallback_plan(intent_result.get('intent', 'general_chat'))
    
    def _get_planning_prompt(self) -> str:
        """Planning Agent 시스템 프롬프트"""
        return """당신은 쇼핑몰 고객 서비스 챗봇의 Planning Agent입니다.
사용자의 요청을 분석하여 최적의 처리 계획을 수립하는 것이 당신의 역할입니다.

## 사용 가능한 에이전트들:
1. **order_agent**: 주문 조회, 배송 상태 확인, 구매 이력 검색
2. **refund_agent**: 환불 가능성 판단, 환불 정책 적용, 환불 수수료 계산
3. **general_agent**: 일반 문의 응답, 최종 응답 정리, 정보 통합

## 계획 수립 원칙:
1. **정보 부족 시 order_agent 우선 호출**: 환불 문의인데 제품 정보나 주문 정보가 불충분하면 order_agent로 먼저 구매 이력을 조회
2. **multi_step 활용**: 복잡한 요청은 여러 에이전트를 순차적으로 활용
3. **컨텍스트 전달**: 이전 단계의 결과를 다음 단계에서 활용할 수 있도록 설계
4. **최종 응답 정리**: 여러 에이전트 결과가 있을 때는 general_agent로 최종 정리

## 계획 예시:

**환불 문의 + 제품명만 있는 경우:**
```json
{
    "plan_type": "multi_step",
    "reason": "제품 정보는 있지만 주문 정보가 부족하므로 구매 이력 조회 후 환불 검토 필요",
    "steps": [
        {
            "step_id": 1,
            "agent": "order_agent", 
            "purpose": "해당 제품의 구매 이력 조회",
            "parameters": {"search_product": "키엘 크림"}
        },
        {
            "step_id": 2,
            "agent": "refund_agent",
            "purpose": "조회된 주문 정보를 바탕으로 환불 가능성 판단",
            "parameters": {"context_from_previous": true}
        }
    ]
}
```

**명확한 주문 조회:**
```json
{
    "plan_type": "single_agent",
    "reason": "명확한 주문 조회 요청으로 order_agent만으로 처리 가능",
    "steps": [
        {
            "step_id": 1,
            "agent": "order_agent",
            "purpose": "주문 상태 조회",
            "parameters": {"order_id": "ORD123"}
        }
    ]
}
```

정확한 JSON 형식으로 응답하세요."""

    def _create_fallback_plan(self, intent: str) -> Dict[str, Any]:
        """파싱 실패시 기본 계획 생성"""
        if intent == 'refund_inquiry':
            return {
                "plan_type": "multi_step",
                "reason": "환불 문의 기본 처리 (파싱 실패로 인한 폴백)",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "order_agent",
                        "purpose": "구매 이력 조회",
                        "parameters": {}
                    },
                    {
                        "step_id": 2,
                        "agent": "refund_agent", 
                        "purpose": "환불 검토",
                        "parameters": {"context_from_previous": True}
                    }
                ],
                "expected_outcome": "환불 가능성 안내"
            }
        elif intent == 'order_status':
            return {
                "plan_type": "single_agent",
                "reason": "주문 조회 기본 처리",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "order_agent",
                        "purpose": "주문 정보 조회",
                        "parameters": {}
                    }
                ],
                "expected_outcome": "주문 상태 안내"
            }
        else:
            return {
                "plan_type": "single_agent", 
                "reason": "일반 문의 처리",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "general_agent",
                        "purpose": "일반 응답",
                        "parameters": {}
                    }
                ],
                "expected_outcome": "일반 문의 응답"
            }
