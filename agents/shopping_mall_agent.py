"""
Shopping Mall Agent - Main LLM-based Agent
"""
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import weave

from tools import (
    CatalogTool, OrderHistoryTool, RefundPolicyTool,
    RefundCalculatorTool, RefundValidatorTool, RefundProcessorTool
)
from agents.intent_classifier import IntentClassifierAgent
from agents.plan_generator import PlanGeneratorAgent
from agents.response_generator import ResponseGeneratorAgent
from agents.conversation_context import ConversationContextAgent
from agents.plan_step import PlanStep


class ShoppingMallAgent:
    """LLM을 활용한 쇼핑몰 챗봇 메인 에이전트"""
    
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
        
        # Initialize LLM agents
        self.intent_classifier = IntentClassifierAgent()
        self.plan_generator = PlanGeneratorAgent()
        self.response_generator = ResponseGeneratorAgent()
        
        # Session management
        self.sessions = {}  # session_id -> ConversationContextAgent
        
    @weave.op()
    def process_message(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process user message with full LLM integration
        """
        # 1. Session management
        if session_id and session_id in self.sessions:
            context = self.sessions[session_id]
        else:
            session_id = str(uuid.uuid4())
            context = ConversationContextAgent(session_id)
            self.sessions[session_id] = context
            
        # 2. Intent classification with conversation history
        conversation_history = context.get_conversation_history(max_turns=3)
        intent, confidence, entities = self.intent_classifier.classify(
            user_input, 
            conversation_history
        )
        
        # Add user message to context
        context.add_user_message(user_input, intent, entities)
        
        # 3. Handle confirmation state
        if context.needs_confirmation():
            return self._handle_confirmation(context, user_input)
            
        # 4. Generate execution plan
        plan = self.plan_generator.generate_plan(
            intent,
            context.get_relevant_context(),
            conversation_history
        )
        
        # 5. Execute plan
        tool_results = self._execute_plan(plan, context)
        
        # 6. Check if confirmation is needed
        needs_confirmation = self._check_needs_confirmation(intent, tool_results)
        if needs_confirmation:
            context.set_pending_action("confirm_refund", {
                "plan": plan,
                "tool_results": tool_results
            })
            
        # 7. Generate response
        response_text = self.response_generator.generate_response(
            intent,
            context.get_relevant_context(),
            tool_results,
            conversation_history,
            needs_confirmation
        )
        
        # Add assistant message to context
        tool_executions = [{"tool": step.tool_name, "status": step.status} for step in plan]
        context.add_assistant_message(response_text, tool_executions)
        
        # 8. Return response
        return {
            "session_id": session_id,
            "response": response_text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "plan": [step.to_dict() for step in plan],
            "tool_results": tool_results,
            "needs_confirmation": needs_confirmation,
            "context_summary": context.get_summary()
        }
        
    @weave.op()
    def _handle_confirmation(self, context: ConversationContextAgent, user_input: str) -> Dict[str, Any]:
        """Handle confirmation response"""
        confirmation = self.intent_classifier.is_confirmation(user_input)
        
        if confirmation is True:
            # Process pending action
            pending_data = context.context.get("pending_data", {})
            
            if context.context.get("pending_action") == "confirm_refund":
                # Execute refund
                plan = pending_data.get("plan", [])
                tool_results = pending_data.get("tool_results", {})
                
                # Add RefundProcessorTool to plan
                refund_step = PlanStep(
                    tool_name="RefundProcessorTool",
                    description="환불 처리 실행",
                    params={
                        "reason": context.context.get("entities", {}).get("refund_reason", "고객 요청"),
                        "customer_note": user_input
                    }
                )
                
                # Execute refund
                result = self._execute_tool(refund_step, tool_results, context)
                tool_results["RefundProcessorTool"] = result
                
                # Generate response
                response_text = self.response_generator.generate_response(
                    "refund_inquiry",
                    context.get_relevant_context(),
                    tool_results,
                    context.get_conversation_history(),
                    False
                )
                
                context.clear_pending_action()
                context.add_assistant_message(response_text)
                
                return {
                    "session_id": context.session_id,
                    "response": response_text,
                    "intent": "refund_confirm",
                    "confidence": 1.0,
                    "confirmation": "accepted",
                    "tool_results": tool_results
                }
                
        elif confirmation is False:
            # Cancel pending action
            context.clear_pending_action()
            response_text = "네, 알겠습니다. 환불을 취소했습니다. 다른 도움이 필요하시면 말씀해주세요."
            context.add_assistant_message(response_text)
            
            return {
                "session_id": context.session_id,
                "response": response_text,
                "intent": "refund_cancel",
                "confidence": 1.0,
                "confirmation": "rejected"
            }
            
        else:
            # Unclear response
            response_text = "환불을 진행하시겠습니까? '네' 또는 '아니요'로 답변해주세요."
            
            return {
                "session_id": context.session_id,
                "response": response_text,
                "intent": "clarification_needed",
                "confidence": 0.5,
                "needs_confirmation": True
            }
            
    def _execute_plan(self, plan: List[PlanStep], context: ConversationContextAgent) -> Dict[str, Any]:
        """Execute plan steps"""
        results = {}
        
        for step in plan:
            # Check dependencies
            can_execute = all(
                dep in results and results[dep].get("success", False)
                for dep in step.depends_on
            )
            
            if not can_execute:
                step.status = "skipped"
                continue
                
            # Execute tool
            result = self._execute_tool(step, results, context)
            results[step.tool_name] = result
            
            # Update context with result
            context.add_tool_result(step.tool_name, result)
            
            step.status = "completed"
            step.result = result
            
        return results
        
    @weave.op()
    def _execute_tool(self, step: PlanStep, previous_results: Dict[str, Any], 
                     context: ConversationContextAgent) -> Dict[str, Any]:
        """Execute a single tool"""
        tool = self.tools.get(step.tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {step.tool_name} not found"}
            
        # Prepare parameters
        params = step.params.copy()
        
        # Auto-fill parameters from previous results
        if step.tool_name == "RefundValidatorTool":
            if "OrderHistoryTool" in previous_results:
                order_result = previous_results["OrderHistoryTool"]
                if order_result.get("success") and order_result.get("orders"):
                    order = order_result["orders"][0]
                    params["order_id"] = order.get("order_id")
                    
        elif step.tool_name == "RefundCalculatorTool":
            if "OrderHistoryTool" in previous_results:
                order_result = previous_results["OrderHistoryTool"]
                if order_result.get("success") and order_result.get("orders"):
                    order = order_result["orders"][0]
                    params["product_price"] = order.get("price", 0)
                    params["delivery_status"] = order.get("delivery_status", "")
                    
        elif step.tool_name == "RefundProcessorTool":
            # Get order_id from context
            if context.context.get("order_context"):
                params["order_id"] = context.context["order_context"].get("order_id")
                
        try:
            return tool.execute(**params)
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    @weave.op()
    def _check_needs_confirmation(self, intent: str, tool_results: Dict[str, Any]) -> bool:
        """Check if confirmation is needed based on results"""
        if intent == "refund_inquiry":
            # Check if refund is possible and not yet processed
            validator_result = tool_results.get("RefundValidatorTool", {})
            processor_result = tool_results.get("RefundProcessorTool", {})
            
            if validator_result.get("refundable") and not processor_result:
                return True
                
        return False
        
    @weave.op()
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session history"""
        if session_id in self.sessions:
            return self.sessions[session_id].to_dict()
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
        
        for session_id, context in self.sessions.items():
            time_diff = current_time - context.updated_at
            if time_diff.total_seconds() > hours * 3600:
                sessions_to_remove.append(session_id)
                
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            
        return len(sessions_to_remove)
