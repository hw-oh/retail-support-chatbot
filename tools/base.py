"""
Base class for all tools in the shopping mall chatbot
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import json


class BaseTool(ABC):
    """모든 툴의 기본 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """툴 실행 메소드 - 각 툴에서 구현해야 함"""
        pass
    
    def __str__(self):
        return f"{self.name}: {self.description}"
    
    def to_dict(self) -> Dict[str, str]:
        """툴 정보를 딕셔너리로 반환"""
        return {
            "name": self.name,
            "description": self.description
        }
