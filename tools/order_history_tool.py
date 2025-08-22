"""
주문 이력 조회 툴
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .base import BaseTool


class OrderHistoryTool(BaseTool):
    """주문 이력을 조회하는 툴"""
    
    def __init__(self, history_path: str = "data/purchase_history.json"):
        super().__init__(
            name="OrderHistoryTool",
            description="고객의 주문 이력을 조회합니다"
        )
        self.history_path = history_path
        self.orders = self._load_orders()
    
    def _load_orders(self) -> List[Dict[str, Any]]:
        """주문 이력 데이터 로드"""
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"경고: {self.history_path} 파일을 찾을 수 없습니다.")
            return []
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        주문 조회 실행
        
        Args:
            order_id: 주문 번호
            product_name: 제품명
            delivery_status: 배송 상태
            start_date: 조회 시작 날짜
            end_date: 조회 종료 날짜
        
        Returns:
            조회 결과
        """
        order_id = kwargs.get('order_id')
        product_name = kwargs.get('product_name')
        delivery_status = kwargs.get('delivery_status')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        # 주문번호로 직접 조회
        if order_id:
            order = self.get_order_by_id(order_id)
            if order:
                return {
                    "success": True,
                    "orders": [order],
                    "count": 1
                }
            else:
                return {
                    "success": False,
                    "orders": [],
                    "count": 0,
                    "message": f"주문번호 {order_id}를 찾을 수 없습니다."
                }
        
        # 조건에 따른 필터링
        results = []
        for order in self.orders:
            if product_name and product_name.lower() not in order['product_name'].lower():
                continue
            
            if delivery_status and order['delivery_status'] != delivery_status:
                continue
            
            if start_date:
                order_date = datetime.strptime(order['purchase_date'], '%Y-%m-%d')
                start = datetime.strptime(start_date, '%Y-%m-%d')
                if order_date < start:
                    continue
            
            if end_date:
                order_date = datetime.strptime(order['purchase_date'], '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if order_date > end:
                    continue
            
            results.append(order)
        
        return {
            "success": True,
            "orders": results,
            "count": len(results)
        }
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문번호로 특정 주문 조회"""
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        return None
    
    def get_order_by_product_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """제품명으로 가장 최근 주문 조회"""
        matching_orders = []
        for order in self.orders:
            if order['product_name'] == product_name:
                matching_orders.append(order)
        
        if not matching_orders:
            return None
        
        # 가장 최근 주문 반환
        matching_orders.sort(key=lambda x: x['purchase_date'], reverse=True)
        return matching_orders[0]
    
    def calculate_days_since_delivery(self, order_id: str) -> Optional[int]:
        """배송 완료 후 경과 일수 계산"""
        order = self.get_order_by_id(order_id)
        if not order or order['delivery_status'] != '배송완료':
            return None
        
        if not order['delivery_date']:
            return None
        
        delivery_date = datetime.strptime(order['delivery_date'], '%Y-%m-%d')
        # 2025년 8월 22일 기준
        today = datetime(2025, 8, 22)
        days_passed = (today - delivery_date).days
        
        return days_passed
