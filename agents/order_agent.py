"""
Order Management Agent
"""
import weave
import json
from typing import List, Dict, Any
from datetime import datetime
from .base import LLMClient
from prompts.weave_prompts import prompt_manager
from config import config


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
        
        # 주문 데이터에 경과일 정보 추가
        raw_orders = self.purchase_data if isinstance(self.purchase_data, list) else self.purchase_data.get('orders', [])
        orders = [self._cal_days_since_delivery(order) for order in raw_orders[:20]]
        
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
{json.dumps(orders, ensure_ascii=False, indent=2)}

## 작업 지시
위 대화 맥락을 고려하여 사용자 요청에 맞는 주문 정보를 찾아서 친절하게 안내해주세요.
- 이전 대화에서 언급된 조건이나 필터가 있다면 적용
- 사용자가 참조하는 이전 정보가 있다면 연결하여 설명
- 환불 등 액션이 필요한 정보는 설명하지 말고 주문 정보만 제공"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
    
    @weave.op()
    def handle_with_order_info(self, user_input: str, context: List[Dict[str, Any]], test_order_info: Dict = None) -> str:
        """평가 시 테스트 케이스의 order_info를 사용한 주문 조회 처리"""
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # 평가 시에는 test_order_info에 경과일 추가, 없으면 기본 데이터 사용
        if test_order_info:
            enriched_order = self._cal_days_since_delivery(test_order_info)
            orders = [enriched_order]
            data_source = "테스트 케이스 주문 정보"
        else:
            raw_orders = self.purchase_data if isinstance(self.purchase_data, list) else self.purchase_data.get('orders', [])
            orders = [self._cal_days_since_delivery(order) for order in raw_orders[:20]]
            data_source = "기본 구매 데이터"
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_order_agent_prompt()
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 주문 데이터 ({data_source})
{json.dumps(orders, ensure_ascii=False, indent=2)}

## 작업 지시
위 대화 맥락을 고려하여 사용자 요청에 맞는 주문 정보를 찾아서 친절하게 안내해주세요.
- 이전 대화에서 언급된 조건이나 필터가 있다면 적용
- 사용자가 참조하는 이전 정보가 있다면 연결하여 설명
- 환불 등 액션이 필요한 정보는 설명하지 말고 주문 정보만 제공"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
    
    @weave.op()
    def handle_with_structured_context(self, user_input: str, structured_context: str, test_order_info: Dict = None) -> str:
        """구조화된 컨텍스트를 사용한 주문 조회 처리"""
        
        # 평가 시에는 test_order_info에 경과일 추가, 없으면 기본 데이터 사용
        if test_order_info:
            enriched_order = self._cal_days_since_delivery(test_order_info)
            orders = [enriched_order]
            data_source = "테스트 케이스 주문 정보"
        else:
            raw_orders = self.purchase_data if isinstance(self.purchase_data, list) else self.purchase_data.get('orders', [])
            orders = [self._cal_days_since_delivery(order) for order in raw_orders[:20]]
            data_source = "기본 구매 데이터"
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_order_agent_prompt()
        user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 구조화된 대화 맥락
{structured_context if structured_context.strip() else "(첫 대화)"}

## 주문 데이터 ({data_source})
{json.dumps(orders, ensure_ascii=False, indent=2)}

## 작업 지시
위 구조화된 대화 맥락을 고려하여 사용자 요청에 맞는 주문 정보를 찾아서 친절하게 안내해주세요.
- 이전 에이전트 결과에서 언급된 조건이나 필터가 있다면 적용
- 사용자가 참조하는 이전 정보가 있다면 연결하여 설명
- 환불 등 액션이 필요한 정보는 설명하지 말고 주문 정보만 제공"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
    
    def _cal_days_since_delivery(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """주문 정보에 간단한 경과일 정보 추가"""
        enriched_order = order.copy()
        
        # 배송 후 경과일 (있는 경우만)
        if order.get("purchase_date"):
            enriched_order["days_since_delivery"] = (datetime.strptime(config.CURRENT_DATE, "%Y-%m-%d") - datetime.strptime(order["purchase_date"], "%Y-%m-%d")).days
        else:
            enriched_order["days_since_delivery"] = None
        
        return enriched_order