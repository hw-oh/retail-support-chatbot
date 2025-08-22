"""
LLM-based Response Generator
"""
from typing import Dict, List, Any, Optional
import json
from agents.base import LLMClient, get_llm_client
from config import config
import weave

class ResponseGeneratorAgent:
    """LLM을 사용한 응답 생성기"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        
    @weave.op()
    def generate_response(self, 
                         intent: str,
                         context: Dict[str, Any],
                         tool_results: Dict[str, Any],
                         conversation_history: List[Dict[str, str]] = None,
                         needs_confirmation: bool = False) -> str:
        """
        컨텍스트와 도구 실행 결과를 기반으로 응답 생성
        """
        messages = self._build_messages(intent, context, tool_results, conversation_history, needs_confirmation)
        
        try:
            response = self.llm.generate(messages, temperature=0.7)
            return response
            
        except Exception as e:
            print(f"Response generation error: {e}")
            # Fallback to template-based response
            return self._fallback_generate_response(intent, tool_results, needs_confirmation)
    
    @weave.op()
    def _build_messages(self, 
                       intent: str,
                       context: Dict[str, Any],
                       tool_results: Dict[str, Any],
                       conversation_history: List[Dict[str, str]] = None,
                       needs_confirmation: bool = False) -> List[Dict[str, str]]:
        """Build messages for LLM"""
        
        system_prompt = f"""You are a helpful customer service assistant for a Korean shopping mall.
Current date: {config.CURRENT_DATE}

Guidelines:
1. Always respond in Korean
2. Be polite and professional
3. Provide clear and concise information
4. Use the tool results to provide accurate information
5. Format prices with commas (e.g., 50,000원)
6. If confirmation is needed, clearly ask for it
7. Use emojis sparingly for friendliness (📦 for orders, 💰 for refunds, 🛍️ for products)

Response style:
- Use honorifics (존댓말)
- Be warm but professional
- Structure information clearly with bullet points or numbered lists when appropriate"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-3:]:
                if turn.get("user"):
                    messages.append({"role": "user", "content": turn["user"]})
                if turn.get("assistant"):
                    messages.append({"role": "assistant", "content": turn["assistant"]})
        
        # Build user message with context
        user_message = f"""Intent: {intent}
Context: {json.dumps(context, ensure_ascii=False)}
Tool Results: {json.dumps(tool_results, ensure_ascii=False)}
Needs Confirmation: {needs_confirmation}

Based on the above information, generate an appropriate response in Korean."""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    @weave.op()
    def _fallback_generate_response(self, intent: str, tool_results: Dict[str, Any], needs_confirmation: bool) -> str:
        """Fallback template-based response generation"""
        
        if intent == "refund_inquiry":
            if "RefundValidatorTool" in tool_results:
                validation = tool_results["RefundValidatorTool"]
                if validation.get("refundable"):
                    if needs_confirmation:
                        return "환불이 가능합니다. 환불을 진행하시겠습니까? (네/아니요)"
                    else:
                        return "환불 처리가 완료되었습니다."
                else:
                    reasons = validation.get("reasons", [])
                    return f"죄송합니다. 환불이 불가능합니다.\n사유: {', '.join(reasons)}"
                    
        elif intent == "order_status":
            if "OrderHistoryTool" in tool_results:
                order_result = tool_results["OrderHistoryTool"]
                if order_result.get("success") and order_result.get("orders"):
                    count = len(order_result["orders"])
                    return f"총 {count}개의 주문을 찾았습니다."
                else:
                    return "주문 정보를 찾을 수 없습니다."
                    
        elif intent == "product_inquiry":
            if "CatalogTool" in tool_results:
                catalog_result = tool_results["CatalogTool"]
                if catalog_result.get("success") and catalog_result.get("products"):
                    count = len(catalog_result["products"])
                    return f"총 {count}개의 제품을 찾았습니다."
                else:
                    return "조건에 맞는 제품을 찾을 수 없습니다."
        
        return "무엇을 도와드릴까요?"
    
    @weave.op()
    def generate_error_response(self, error_type: str, error_details: str = None) -> str:
        """Generate error response"""
        messages = [
            {
                "role": "system",
                "content": "Generate a polite error message in Korean for a customer service chatbot."
            },
            {
                "role": "user",
                "content": f"Error type: {error_type}\nDetails: {error_details or 'None'}"
            }
        ]
        
        try:
            return self.llm.generate(messages, temperature=0.5, max_tokens=200)
        except:
            # Fallback error messages
            error_messages = {
                "order_not_found": "죄송합니다. 주문 정보를 찾을 수 없습니다. 주문번호를 다시 확인해주세요.",
                "system_error": "시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "invalid_request": "요청을 처리할 수 없습니다. 다시 한 번 말씀해주세요.",
                "default": "죄송합니다. 요청을 처리하는 중 문제가 발생했습니다."
            }
            
            return error_messages.get(error_type, error_messages["default"])
    
    @weave.op()
    def generate_clarification_request(self, missing_info: str, context: Dict[str, Any] = None) -> str:
        """Generate clarification request"""
        messages = [
            {
                "role": "system",
                "content": "Generate a polite clarification request in Korean for missing information."
            },
            {
                "role": "user",
                "content": f"Missing information: {missing_info}\nContext: {json.dumps(context or {}, ensure_ascii=False)}"
            }
        ]
        
        try:
            return self.llm.generate(messages, temperature=0.6, max_tokens=150)
        except:
            # Fallback clarification messages
            clarification_messages = {
                "order_id": "주문번호를 알려주시겠어요?",
                "product_name": "어떤 제품을 찾으시나요?",
                "time_period": "언제 주문하신 건지 알려주시겠어요?",
                "default": "좀 더 자세히 말씀해주시겠어요?"
            }
            
            return clarification_messages.get(missing_info, clarification_messages["default"])
