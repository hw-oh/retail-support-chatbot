"""
Enhanced Conversation Context Management
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class ConversationContextAgent:
    """Enhanced conversation context with full history tracking"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Full conversation history
        self.messages = []  # List of all messages (user and assistant)
        
        # Structured context
        self.context = {
            "current_intent": None,
            "entities": {},
            "pending_action": None,
            "order_context": None,
            "tool_results": {},
            "confirmation_state": None
        }
        
        # Execution history
        self.execution_history = []  # List of all tool executions
        
    def add_user_message(self, message: str, intent: str = None, entities: Dict[str, Any] = None):
        """Add user message to history"""
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "entities": entities or {}
        })
        
        if intent:
            self.context["current_intent"] = intent
        if entities:
            self.context["entities"].update(entities)
            
        self.updated_at = datetime.now()
        
    def add_assistant_message(self, message: str, tool_executions: List[Dict[str, Any]] = None):
        """Add assistant message to history"""
        self.messages.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "tool_executions": tool_executions or []
        })
        
        if tool_executions:
            self.execution_history.extend(tool_executions)
            
        self.updated_at = datetime.now()
        
    def add_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """Add tool execution result"""
        self.context["tool_results"][tool_name] = result
        
        # Update context based on tool results
        if tool_name == "OrderHistoryTool" and result.get("success"):
            orders = result.get("orders", [])
            if len(orders) == 1:
                self.context["order_context"] = orders[0]
            elif len(orders) > 1:
                self.context["multiple_orders"] = orders
                
        self.updated_at = datetime.now()
        
    def get_conversation_history(self, max_turns: int = None) -> List[Dict[str, str]]:
        """Get conversation history for LLM context"""
        history = []
        
        messages_to_process = self.messages
        if max_turns:
            # Get last N turns (user + assistant pairs)
            messages_to_process = self.messages[-(max_turns * 2):]
            
        for msg in messages_to_process:
            if msg["role"] == "user":
                history.append({"user": msg["content"]})
            elif msg["role"] == "assistant":
                if history and "assistant" not in history[-1]:
                    history[-1]["assistant"] = msg["content"]
                else:
                    history.append({"assistant": msg["content"]})
                    
        return history
    
    def get_relevant_context(self) -> Dict[str, Any]:
        """Get relevant context for current conversation state"""
        return {
            "current_intent": self.context.get("current_intent"),
            "entities": self.context.get("entities", {}),
            "order_context": self.context.get("order_context"),
            "pending_action": self.context.get("pending_action"),
            "recent_tools": list(self.context.get("tool_results", {}).keys())[-3:],
            "turn_count": len([m for m in self.messages if m["role"] == "user"])
        }
    
    def needs_confirmation(self) -> bool:
        """Check if confirmation is needed"""
        return self.context.get("pending_action") in ["confirm_refund", "confirm_order_selection"]
    
    def set_pending_action(self, action: str, data: Dict[str, Any] = None):
        """Set pending action that needs confirmation"""
        self.context["pending_action"] = action
        self.context["pending_data"] = data
        
    def clear_pending_action(self):
        """Clear pending action"""
        self.context["pending_action"] = None
        self.context["pending_data"] = None
        
    def get_summary(self) -> str:
        """Get conversation summary for logging"""
        return {
            "session_id": self.session_id,
            "turn_count": len([m for m in self.messages if m["role"] == "user"]),
            "current_intent": self.context.get("current_intent"),
            "has_order_context": bool(self.context.get("order_context")),
            "tools_used": list(self.context.get("tool_results", {}).keys()),
            "duration": (self.updated_at - self.created_at).total_seconds()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export full context"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "context": self.context,
            "execution_history": self.execution_history
        }
