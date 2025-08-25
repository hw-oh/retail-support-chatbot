"""
Shopping Mall Agent - 대화형 상호작용 기반 메인 에이전트
"""
from typing import Dict, List, Any, Optional, Tuple
import uuid
import json
from datetime import datetime
import weave

from tools import (
    CatalogTool, OrderHistoryTool, RefundPolicyTool,
    RefundCalculatorTool, RefundValidatorTool, RefundProcessorTool
)
from agents.intent_classifier import IntentClassifierAgent
from agents.response_generator import ResponseGeneratorAgent
from agents.conversation_context import ConversationContextAgent
from agents.base import LLMClient, get_llm_client


class DialogState:
    """대화 상태 관리"""
    def __init__(self):
        self.current_intent = None
        self.current_entities = {}
        self.tool_results_cache = {}  # 이전 도구 실행 결과 캐시
        self.active_context = {}  # 현재 활성화된 컨텍스트 (예: 선택된 주문)
        self.pending_actions = []  # 대기 중인 작업들
        self.dialog_phase = "init"  # init, exploring, confirming, executing


class ShoppingMallAgent:
    """LLM을 활용한 쇼핑몰 챗봇 메인 에이전트 - Multi-turn 대화 지원"""
    
    def __init__(self):
        # Initialize tools
        self.tools = {
            "CatalogTool": CatalogTool(),
            "OrderHistoryTool": OrderHistoryTool(),
            "RefundPolicyTool": RefundPolicyTool(),
            "RefundCalculatorTool": RefundCalculatorTool(),
            "RefundValidatorTool": RefundValidatorTool(),
            "RefundProcessorTool": RefundProcessorTool()
        }
        
        # Initialize agents
        self.intent_classifier = IntentClassifierAgent()
        self.response_generator = ResponseGeneratorAgent()
        self.llm = get_llm_client()
        
        # Session management
        self.sessions = {}  # session_id -> (ConversationContextAgent, DialogState)
        
    @weave.op()
    def process_message(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        대화형 메시지 처리 - 동적으로 다음 액션 결정
        """
        # 1. Session management
        if session_id and session_id in self.sessions:
            context, dialog_state = self.sessions[session_id]
        else:
            session_id = str(uuid.uuid4())
            context = ConversationContextAgent(session_id)
            dialog_state = DialogState()
            self.sessions[session_id] = (context, dialog_state)
            
        # 2. Intent classification with conversation history
        conversation_history = context.get_conversation_history(max_turns=5)
        intent, confidence, entities = self.intent_classifier.classify(
            user_input, 
            conversation_history
        )
        
        # Add user message to context
        context.add_user_message(user_input, intent, entities)
        
        # 3. Dialog state update
        dialog_state.current_intent = intent
        dialog_state.current_entities.update(entities)
        
        # 4. Dynamic action determination based on current state
        action_plan = self._determine_next_action(
            intent, entities, dialog_state, conversation_history
        )
        
        # 5. Execute immediate actions
        tool_results = {}
        for action in action_plan:
            if action["type"] == "tool_execution":
                result = self._execute_tool(
                    action["tool_name"], 
                    action["params"], 
                    dialog_state
                )
                tool_results[action["tool_name"]] = result
                dialog_state.tool_results_cache[action["tool_name"]] = result
                
                # OrderHistoryTool 결과를 active_context에 저장
                if action["tool_name"] == "OrderHistoryTool" and result.get("success"):
                    orders = result.get("orders", [])
                    if orders:
                        dialog_state.active_context["available_orders"] = orders
                        dialog_state.active_context["has_order_history"] = True
                
            elif action["type"] == "context_update":
                dialog_state.active_context.update(action["context"])
                
            elif action["type"] == "clarification_needed":
                # 추가 정보가 필요한 경우
                break
                
        # 6. Generate response based on current state
        response_text = self._generate_contextual_response(
            intent,
            dialog_state,
            tool_results,
            conversation_history,
            action_plan
        )
        
        # Add assistant message to context
        context.add_assistant_message(response_text, list(tool_results.keys()))
        
        # 7. Return response
        return {
            "session_id": session_id,
            "response": response_text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "tool_results": tool_results,
            "dialog_state": {
                "phase": dialog_state.dialog_phase,
                "active_context": dialog_state.active_context,
                "cached_results": list(dialog_state.tool_results_cache.keys())
            },
            "context_summary": context.get_summary()
        }
        
    @weave.op()
    def _determine_next_action(self, intent: str, entities: Dict[str, Any], 
                              dialog_state: DialogState, 
                              conversation_history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        현재 대화 상태를 기반으로 다음 액션 결정
        LLM을 사용하여 동적으로 결정
        """
        # Build context for decision
        context_summary = {
            "current_intent": intent,
            "entities": entities,
            "previous_results": {
                k: {"success": v.get("success", False), 
                    "summary": self._summarize_result(v)}
                for k, v in dialog_state.tool_results_cache.items()
            },
            "active_context": dialog_state.active_context,
            "dialog_phase": dialog_state.dialog_phase
        }
        
        # Use LLM to determine next actions
        messages = [
            {
                "role": "system",
                "content": """You are a dialog action planner for a Korean shopping mall chatbot. Based on the current dialog state and user intent, 
determine the next actions to take. Consider:
1. What information is already available from previous tool calls
2. What new information is needed
3. Whether to execute tools, ask for clarification, or provide information

CRITICAL RULES FOR INTENT HANDLING:

1. For "order_status" intent:
   - ALWAYS execute OrderHistoryTool
   - NEVER ask for order numbers
   - Use time_reference and quantity entities if provided

2. For "clarification" intent (user refers to previous conversation):
   - Check active_context for available_orders
   - If refund_reference is true and has_order_history is true:
     → Create MULTIPLE actions: one RefundValidatorTool execution for EACH order
     → Example: If 3 orders exist, return 3 separate tool_execution actions
     → NEVER combine multiple orders into one action
   - If selection_type is "other":
     → Execute RefundValidatorTool for orders not yet checked in tool_results_cache
   - Examples:
     * "그 중에 뭘 환불할 수 있어?" → Return MULTIPLE actions like:
       [{"type": "tool_execution", "tool_name": "RefundValidatorTool", "params": {"order_id": "ORD001"}},
        {"type": "tool_execution", "tool_name": "RefundValidatorTool", "params": {"order_id": "ORD002"}},
        {"type": "tool_execution", "tool_name": "RefundValidatorTool", "params": {"order_id": "ORD003"}}]
     * "다른 물건을 환불하고 싶어" → Check unchecked orders

3. For "refund_inquiry" intent:
   - If has_order_history is true and available_orders exists:
     → Execute RefundValidatorTool for available orders
   - If no context available:
     → Ask for order information in Korean

CONTEXT AWARENESS:
- active_context.has_order_history: true if order history was retrieved
- active_context.available_orders: list of orders from previous query
- tool_results_cache: contains previous tool execution results

RESPONSE RULES:
- ALWAYS use Korean for clarification questions
- NEVER ask for information already in context
- Prefer tool execution over clarification when possible
- Return MULTIPLE actions when checking multiple orders (don't batch them)

Output a list of actions in JSON format. Each action should be a separate object in the array."""
            },
            {
                "role": "user",
                "content": f"""Current state: {context_summary}
Recent conversation: {conversation_history[-3:] if conversation_history else []}

User intent: {intent}
User entities: {entities}
Available orders (first 10): {[{'order_id': o['order_id'], 'product': o['product_name']} for o in dialog_state.active_context.get('available_orders', [])[:10]]}
Already checked with RefundValidatorTool: {[k for k in dialog_state.tool_results_cache.keys() if k.startswith('RefundValidatorTool_')]}

Determine next actions. Each action should have:
- type: "tool_execution", "context_update", or "clarification_needed"
- tool_name: (if tool_execution)
- params: (if tool_execution)
- context: (if context_update)
- question: (if clarification_needed, MUST be in Korean)

IMPORTANT: For clarification intent with refund_reference, create actions for ALL available orders (limit to 5-7 for practical reasons).
For "다른" (other) selection_type, EXCLUDE already checked orders."""
            }
        ]
        
        schema = {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "params": {"type": "object"},
                            "context": {"type": "object"},
                            "question": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        try:
            result = self.llm.generate_json(messages, schema=schema)
            actions = result.get("actions", [])
            print(f"[DEBUG] LLM generated {len(actions)} actions")
            for i, action in enumerate(actions):
                print(f"[DEBUG] Action {i+1}: {action}")
            return actions
        except Exception as e:
            print(f"[ERROR] LLM action determination failed: {e}")
            # 에러 시에도 기본 액션 반환
            return [{
                "type": "context_update",
                "context": {"error": str(e)}
            }]

        
    def _execute_tool(self, tool_name: str, params: Dict[str, Any], 
                     dialog_state: DialogState) -> Dict[str, Any]:
        """도구 실행"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found"}
            
        # Auto-fill parameters from dialog state if needed
        enriched_params = self._enrich_params(tool_name, params, dialog_state)
        
        try:
            return tool.execute(**enriched_params)
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _enrich_params(self, tool_name: str, params: Dict[str, Any], 
                      dialog_state: DialogState) -> Dict[str, Any]:
        """대화 상태를 기반으로 파라미터 보강"""
        enriched = params.copy()
        
        # 예: RefundValidatorTool이 order_id가 필요한데 없으면 active_context에서 가져옴
        if tool_name == "RefundValidatorTool" and "order_id" not in enriched:
            if dialog_state.active_context.get("selected_order"):
                enriched["order_id"] = dialog_state.active_context["selected_order"]["order_id"]
                
        return enriched
        
    def _generate_contextual_response(self, intent: str, dialog_state: DialogState,
                                    tool_results: Dict[str, Any],
                                    conversation_history: List[Dict[str, str]],
                                    action_plan: List[Dict[str, Any]]) -> str:
        """컨텍스트를 고려한 응답 생성"""
        # Check if clarification is needed
        for action in action_plan:
            if action["type"] == "clarification_needed":
                return action["question"]
                
        # Use response generator with enriched context
        enriched_context = {
            "active_context": dialog_state.active_context,
            "all_results": dialog_state.tool_results_cache,
            "current_results": tool_results
        }
        
        return self.response_generator.generate_response(
            intent,
            enriched_context,
            tool_results,
            conversation_history,
            needs_confirmation=False
        )
        
    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """도구 실행 결과 요약"""
        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"
            
        # 각 도구별 요약 로직
        if "orders" in result:
            return f"{len(result['orders'])} orders found"
        elif "refundable" in result:
            return f"Refundable: {result['refundable']}"
        elif "products" in result:
            return f"{len(result['products'])} products found"
            
        return "Success"
        
    def _calculate_date_range(self, time_reference: str) -> Tuple[str, str]:
        """시간 참조를 날짜 범위로 변환"""
        from datetime import datetime, timedelta
        from config import config
        
        current_date = datetime.strptime(config.CURRENT_DATE, "%Y-%m-%d")
        
        if "일주일" in time_reference:
            start = current_date - timedelta(days=7)
        elif "한달" in time_reference:
            start = current_date - timedelta(days=30)
        elif "어제" in time_reference:
            start = current_date - timedelta(days=1)
            current_date = start
        else:
            start = current_date - timedelta(days=7)  # 기본값
            
        return start.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")
        
    @weave.op()
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session history"""
        if session_id in self.sessions:
            context, dialog_state = self.sessions[session_id]
            return {
                "conversation_history": context.get_conversation_history(),
                "dialog_state": {
                    "active_context": dialog_state.active_context,
                    "cached_results": list(dialog_state.tool_results_cache.keys())
                }
            }
        return None
        
    @weave.op()
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
    @weave.op()
    def cleanup_old_sessions(self, hours: int = 24):
        """Clean up old sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, (context, _) in self.sessions.items():
            time_diff = current_time - context.updated_at
            if time_diff.total_seconds() > hours * 3600:
                sessions_to_remove.append(session_id)
                
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            
        return len(sessions_to_remove)
