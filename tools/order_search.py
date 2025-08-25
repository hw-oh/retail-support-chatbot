"""
Order Search Tool
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .data_loader import DataLoader


class OrderSearchTool:
    """주문 검색 도구"""
    
    def __init__(self):
        self.data = DataLoader.load_purchase_history()
    
    def search_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문번호로 검색"""
        orders = self.data if isinstance(self.data, list) else self.data.get('orders', [])
        for order in orders:
            if order.get('order_id') == order_id:
                return order
        return None
    
    def search_recent_orders(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 주문 검색"""
        orders = self.data if isinstance(self.data, list) else self.data.get('orders', [])
        # 날짜순 정렬 (최신순)
        sorted_orders = sorted(orders, key=lambda x: x.get('order_date', ''), reverse=True)
        return sorted_orders[:limit]
    
    def search_by_product(self, product_name: str) -> List[Dict[str, Any]]:
        """상품명으로 검색"""
        orders = self.data if isinstance(self.data, list) else self.data.get('orders', [])
        matching_orders = []
        
        for order in orders:
            items = order.get('items', [])
            for item in items:
                if product_name.lower() in item.get('product_name', '').lower():
                    matching_orders.append(order)
                    break
        
        return matching_orders
    
    def search_by_date_range(self, days_ago: int) -> List[Dict[str, Any]]:
        """특정 기간 내 주문 검색"""
        orders = self.data if isinstance(self.data, list) else self.data.get('orders', [])
        cutoff_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        matching_orders = []
        for order in orders:
            order_date = order.get('order_date', '')
            if order_date >= cutoff_date:
                matching_orders.append(order)
        
        return matching_orders
