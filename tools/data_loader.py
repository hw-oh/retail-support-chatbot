"""
Data Loading Tool
"""
import json
from typing import Dict, Any


class DataLoader:
    """데이터 로딩 유틸리티"""
    
    @staticmethod
    def load_purchase_history() -> Dict[str, Any]:
        """구매 내역 데이터 로드"""
        with open('data/purchase_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def load_refund_policy() -> str:
        """환불 정책 로드"""
        with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def load_catalog() -> Dict[str, Any]:
        """상품 카탈로그 로드"""
        with open('data/catalog.json', 'r', encoding='utf-8') as f:
            return json.load(f)
