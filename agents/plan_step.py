"""
Plan Step class for execution planning
"""
from typing import Dict, List, Any, Optional


class PlanStep:
    """계획의 각 단계를 나타내는 클래스"""
    
    def __init__(self, tool_name: str, description: str, params: Dict[str, Any] = None,
                 depends_on: List[str] = None):
        self.tool_name = tool_name
        self.description = description
        self.params = params or {}
        self.depends_on = depends_on or []
        self.result = None
        self.status = "pending"  # pending, in_progress, completed, failed
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "description": self.description,
            "params": self.params,
            "depends_on": self.depends_on,
            "status": self.status
        }
