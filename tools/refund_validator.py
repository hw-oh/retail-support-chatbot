"""
Refund Validation Tool
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .data_loader import DataLoader


class RefundValidatorTool:
    """환불 검증 도구"""
    
    def __init__(self):
        self.policy = DataLoader.load_refund_policy()
        self.purchase_data = DataLoader.load_purchase_history()
    
    def validate_refund_eligibility(self, order_id: str, product_name: str = None) -> Dict[str, Any]:
        """환불 가능 여부 검증"""
        
        # 주문 찾기
        order = self._find_order(order_id)
        if not order:
            return {
                "eligible": False,
                "reason": "주문을 찾을 수 없습니다.",
                "order": None
            }
        
        # 날짜 확인 (7일 이내)
        order_date_str = order.get('order_date') or order.get('purchase_date')
        order_date = datetime.strptime(order_date_str, '%Y-%m-%d')
        days_since_order = (datetime.now() - order_date).days
        
        if days_since_order > 7:
            return {
                "eligible": False,
                "reason": "주문일로부터 7일이 경과하여 환불이 불가능합니다.",
                "order": order,
                "days_since_order": days_since_order
            }
        
        # 배송 상태 확인
        status = order.get('status') or order.get('delivery_status', '')
        if status in ['배송완료', '구매확정']:
            return {
                "eligible": True,
                "reason": "환불 가능합니다.",
                "order": order,
                "days_since_order": days_since_order,
                "remaining_days": 7 - days_since_order
            }
        elif status == '배송중':
            return {
                "eligible": False,
                "reason": "배송 중인 상품은 배송완료 후 환불 신청 가능합니다.",
                "order": order
            }
        else:
            return {
                "eligible": True,
                "reason": "환불 가능합니다.",
                "order": order,
                "days_since_order": days_since_order,
                "remaining_days": 7 - days_since_order
            }
    
    def _find_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문 찾기"""
        orders = self.purchase_data if isinstance(self.purchase_data, list) else self.purchase_data.get('orders', [])
        for order in orders:
            if order.get('order_id') == order_id:
                return order
        return None
