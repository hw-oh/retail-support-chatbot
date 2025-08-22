"""
LLM-based Plan Generator
"""
from typing import Dict, List, Any, Optional
import json
from agents.base import LLMClient, get_llm_client
from agents.plan_step import PlanStep
from config import config
import weave

class PlanGeneratorAgent:
    """LLM을 사용한 계획 생성기"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        
        # Available tools description
        self.tool_descriptions = {
            "CatalogTool": {
                "description": "제품 카탈로그에서 제품을 검색합니다",
                "params": ["product_name", "category", "min_price", "max_price"]
            },
            "OrderHistoryTool": {
                "description": "주문 이력을 조회합니다",
                "params": ["order_id", "product_name", "start_date", "end_date", "delivery_status"]
            },
            "RefundPolicyTool": {
                "description": "환불 정책 정보를 조회합니다",
                "params": ["query_type", "delivery_status", "product_name", "category"]
            },
            "RefundValidatorTool": {
                "description": "환불 가능 여부를 검증합니다",
                "params": ["order_id", "is_defective", "has_usage_trace"]
            },
            "RefundCalculatorTool": {
                "description": "환불 수수료와 금액을 계산합니다",
                "params": ["product_price", "delivery_status", "is_defective"]
            },
            "RefundProcessorTool": {
                "description": "환불을 처리합니다",
                "params": ["order_id", "reason", "customer_note"]
            }
        }
        
        # Plan schema
        self.plan_schema = {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "description": {"type": "string"},
                            "params": {"type": "object"},
                            "depends_on": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["tool_name", "description", "params"]
                    }
                },
                "reasoning": {"type": "string"}
            },
            "required": ["steps", "reasoning"]
        }
        
    @weave.op()
    def generate_plan(self, intent: str, context: Dict[str, Any], conversation_history: List[Dict[str, str]] = None) -> List[PlanStep]:
        """
        의도와 컨텍스트를 기반으로 실행 계획 생성
        """
        messages = self._build_messages(intent, context, conversation_history)
        
        try:
            result = self.llm.generate_json(messages, schema=self.plan_schema)
            
            steps = []
            for step_data in result.get("steps", []):
                step = PlanStep(
                    tool_name=step_data["tool_name"],
                    description=step_data["description"],
                    params=step_data.get("params", {}),
                    depends_on=step_data.get("depends_on", [])
                )
                steps.append(step)
            
            return steps
            
        except Exception as e:
            print(f"Plan generation error: {e}")
            # Fallback to rule-based planning
            return self._fallback_generate_plan(intent, context)
    
    @weave.op()
    def _build_messages(self, intent: str, context: Dict[str, Any], conversation_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build messages for LLM"""
        tools_info = json.dumps(self.tool_descriptions, indent=2, ensure_ascii=False)
        
        system_prompt = f"""You are a plan generator for a Korean shopping mall customer service chatbot.
Current date: {config.CURRENT_DATE}

Given a user intent and context, generate a step-by-step plan using available tools.
Each step should specify:
- tool_name: The tool to use
- description: What this step does
- params: Parameters for the tool
- depends_on: List of tools that must complete before this step

Available tools:
{tools_info}

Important rules:
1. For refund inquiries, always check order first, then validate refund eligibility, calculate fees, and process if confirmed
2. For date-based queries, calculate start_date and end_date based on current date
3. Tools that depend on previous results should specify dependencies
4. RefundProcessorTool should only be included if user has confirmed the refund"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        if conversation_history:
            history_summary = "Previous conversation:\n"
            for turn in conversation_history[-3:]:
                history_summary += f"User: {turn.get('user', '')}\n"
                history_summary += f"Assistant: {turn.get('assistant', '')}\n"
            messages.append({"role": "system", "content": history_summary})
        
        # Current request
        user_message = f"""Intent: {intent}
Context: {json.dumps(context, ensure_ascii=False)}

Generate a plan to handle this request."""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    @weave.op()
    def _fallback_generate_plan(self, intent: str, context: Dict[str, Any]) -> List[PlanStep]:
        """Fallback rule-based plan generation"""
        steps = []
        
        if intent == "refund_inquiry":
            # Check if we have order info
            if context.get("order_id"):
                steps.append(PlanStep(
                    tool_name="OrderHistoryTool",
                    description="주문 정보 조회",
                    params={"order_id": context["order_id"]}
                ))
                steps.append(PlanStep(
                    tool_name="RefundValidatorTool",
                    description="환불 가능 여부 검증",
                    params={},
                    depends_on=["OrderHistoryTool"]
                ))
                steps.append(PlanStep(
                    tool_name="RefundCalculatorTool",
                    description="환불 금액 계산",
                    params={},
                    depends_on=["RefundValidatorTool"]
                ))
                
        elif intent == "order_status":
            params = {}
            if context.get("order_id"):
                params["order_id"] = context["order_id"]
            elif context.get("time_reference"):
                # Simple date calculation
                if "일주일" in context["time_reference"]:
                    from datetime import datetime, timedelta
                    today = datetime(2025, 8, 22)
                    start = today - timedelta(days=7)
                    params["start_date"] = start.strftime("%Y-%m-%d")
                    params["end_date"] = today.strftime("%Y-%m-%d")
                    
            steps.append(PlanStep(
                tool_name="OrderHistoryTool",
                description="주문 내역 조회",
                params=params
            ))
            
        elif intent == "product_inquiry":
            params = {}
            if context.get("category"):
                params["category"] = context["category"]
            if context.get("max_price"):
                params["max_price"] = context["max_price"]
                
            steps.append(PlanStep(
                tool_name="CatalogTool",
                description="제품 검색",
                params=params
            ))
        
        return steps
    
    @weave.op()
    def adapt_plan(self, current_plan: List[PlanStep], tool_results: Dict[str, Any], user_feedback: str = None) -> List[PlanStep]:
        """
        Adapt plan based on tool results and user feedback
        """
        messages = [
            {
                "role": "system",
                "content": "You are adapting an execution plan based on results and feedback. Modify or extend the plan as needed."
            },
            {
                "role": "user",
                "content": f"""Current plan: {[step.to_dict() for step in current_plan]}
Tool results so far: {json.dumps(tool_results, ensure_ascii=False)}
User feedback: {user_feedback or 'None'}

Should the plan be modified? If yes, provide the updated plan."""
            }
        ]
        
        try:
            result = self.llm.generate_json(messages, schema=self.plan_schema)
            
            # Convert to PlanStep objects
            new_steps = []
            for step_data in result.get("steps", []):
                # Skip already completed steps
                if any(s.tool_name == step_data["tool_name"] and s.status == "completed" for s in current_plan):
                    continue
                    
                step = PlanStep(
                    tool_name=step_data["tool_name"],
                    description=step_data["description"],
                    params=step_data.get("params", {}),
                    depends_on=step_data.get("depends_on", [])
                )
                new_steps.append(step)
            
            return new_steps
            
        except Exception as e:
            print(f"Plan adaptation error: {e}")
            return []  # Return empty list on error
