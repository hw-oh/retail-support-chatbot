"""
LLM-based Intent Classifier
"""
from typing import Dict, List, Any, Tuple, Optional
import json
from agents.base import LLMClient, get_llm_client
from config import config
import weave

class IntentClassifierAgent:
    """LLM을 사용한 의도 분류기"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        
        # Intent schema for structured output
        self.intent_schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["refund_inquiry", "order_status", "product_inquiry", "clarification", "general_chat"],
                    "description": "사용자의 주요 의도"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "의도 분류 신뢰도"
                },
                "entities": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "pattern": "^ORD\\d+$"},
                        "product_name": {"type": "string"},
                        "time_reference": {"type": "string"},
                        "refund_reason": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "refund_reference": {"type": "boolean", "description": "True if user mentions refund in clarification"},
                        "selection_type": {"type": "string", "enum": ["first", "second", "third", "other", "specific"], "description": "Type of selection user is making"},
                        "reference_context": {"type": "string", "description": "What the user is referring to from previous conversation"},
                        "price_range": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"}
                            }
                        }
                    }
                },
                "sub_intents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "추가적인 세부 의도들"
                }
            },
            "required": ["intent", "confidence", "entities"]
        }

    @weave.op()
    def classify(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, float, Dict[str, Any]]:
        """
        사용자 입력의 의도를 분류
        
        Returns:
            (의도, 신뢰도, 추출된 엔티티)
        """
        messages = self._build_messages(user_input, conversation_history)
        
        try:
            result = self.llm.generate_json(messages, schema=self.intent_schema)
            
            intent = result.get("intent", "general_chat")
            confidence = result.get("confidence", 0.5)
            entities = result.get("entities", {})
            
            # Clean up empty entities
            entities = {k: v for k, v in entities.items() if v}
            
            return intent, confidence, entities
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            # Return default values on error
            return "general_chat", 0.5, {}
    
    @weave.op()
    def _build_messages(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build messages for LLM"""
        system_prompt = f"""You are an intent classifier for a Korean shopping mall customer service chatbot.
Current date: {config.CURRENT_DATE}

Classify user intents into one of these categories:
- refund_inquiry: 환불, 취소, 반품 관련 문의
- order_status: 주문 상태, 배송 추적, 구매 내역/주문 내역 조회 (구매내역, 주문내역, 주문 조회 등)
- product_inquiry: 제품 검색, 가격 문의, 상품 추천
- clarification: 이전 대화 참조, 선택, 추가 정보 제공 (그 중에, 다른 것, 첫 번째, 두 번째, 위에서 말한 것 등)
- general_chat: 인사, 감사, 일반 대화

Also extract relevant entities:
- order_id: 주문번호 (ORD로 시작하는 숫자)
- product_name: 제품명
- time_reference: 시간 표현 (어제, 지난주, 3일 전, 일주일 동안, 최근, 일주일 이내 등)
- refund_reason: 환불 사유
- quantity: 수량 (5개, 3개 등에서 숫자 추출)
- refund_reference: clarification에서 환불을 언급하면 true
- selection_type: 선택 유형 (first/second/third/other/specific)
- reference_context: 이전 대화에서 참조하는 내용
- price_range: 가격 범위

Important:
- "구매내역" or "주문내역" MUST be classified as order_status
- Extract numbers from phrases like "최근 구매내역 5개" as quantity
- "최근" or "일주일 이내" should be extracted as time_reference
- When user refers to previous conversation ("그 중에", "이 중에", "위에서", "다른 것"), classify as clarification
- If user is making a selection or providing additional info about previous topic, classify as clarification
- Examples of clarification: "그 중에 뭘 환불할 수 있어?", "다른 물건을 환불하고 싶어", "첫 번째 것", "마우스 말고 다른 거"

Consider the conversation history for context. If the user is clearly referring to previous messages, it's likely clarification."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for turn in conversation_history[-3:]:  # Last 3 turns for context
                messages.append({"role": "user", "content": turn.get("user", "")})
                messages.append({"role": "assistant", "content": turn.get("assistant", "")})
        
        messages.append({"role": "user", "content": user_input})
        
        return messages
    

    
    def is_confirmation(self, user_input: str) -> Optional[bool]:
        """Check if user input is a confirmation/denial"""
        messages = [
            {
                "role": "system",
                "content": "Determine if the user input is a confirmation (yes/agree), denial (no/disagree), or unclear. Respond with only 'yes', 'no', or 'unclear'."
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        try:
            response = self.llm.generate(messages, temperature=0.1, max_tokens=10)
            response = response.strip().lower()
            
            if response == "yes":
                return True
            elif response == "no":
                return False
            else:
                return None
                
        except Exception as e:
            print(f"Confirmation check error: {e}")
            # Fallback to keyword matching
            positive = ["네", "예", "응", "맞아", "좋아", "확인", "진행"]
            negative = ["아니", "안", "취소", "그만", "싫어"]
            
            input_lower = user_input.lower()
            if any(word in input_lower for word in positive):
                return True
            elif any(word in input_lower for word in negative):
                return False
            return None
