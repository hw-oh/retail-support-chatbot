"""
환불 가능 여부 검증 툴
"""
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from .base import BaseTool
from .order_history_tool import OrderHistoryTool
from .refund_policy_tool import RefundPolicyTool


class RefundValidatorTool(BaseTool):
    """환불 가능 여부를 검증하는 툴"""
    
    def __init__(self, order_tool: Optional[OrderHistoryTool] = None, 
                 policy_tool: Optional[RefundPolicyTool] = None):
        super().__init__(
            name="RefundValidatorTool",
            description="주문의 환불 가능 여부를 검증합니다"
        )
        self.order_tool = order_tool or OrderHistoryTool()
        self.policy_tool = policy_tool or RefundPolicyTool()
        self.refund_period_days = 7
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        환불 가능 여부 검증 실행
        
        Args:
            order_id: 주문 번호
            product_name: 제품명 (order_id가 없을 경우)
            is_defective: 불량품 여부
            has_usage_trace: 사용 흔적 여부
        
        Returns:
            검증 결과
        """
        order_id = kwargs.get('order_id')
        product_name = kwargs.get('product_name')
        is_defective = kwargs.get('is_defective', False)
        has_usage_trace = kwargs.get('has_usage_trace', False)
        
        # 주문 정보 조회
        order = None
        if order_id:
            order = self.order_tool.get_order_by_id(order_id)
        elif product_name:
            order = self.order_tool.get_order_by_product_name(product_name)
        
        if not order:
            return {
                "success": False,
                "refundable": False,
                "reason": "주문 정보를 찾을 수 없습니다.",
                "details": {}
            }
        
        # 검증 수행
        validation_results = self._perform_validation(order, is_defective, has_usage_trace)
        
        return validation_results
    
    def _perform_validation(self, order: Dict[str, Any], 
                          is_defective: bool, has_usage_trace: bool) -> Dict[str, Any]:
        """환불 가능 여부 상세 검증"""
        
        reasons = []
        refundable = True
        
        # 1. 배송 상태 확인
        delivery_status = order.get('delivery_status', '')
        status_policy = self.policy_tool.execute(
            query_type='status_policy', 
            delivery_status=delivery_status
        )
        
        if not status_policy['success'] or not status_policy['policy'].get('cancellable', False):
            refundable = False
            reasons.append(f"{delivery_status} 상태에서는 환불이 불가능합니다.")
        
        # 2. 환불 기간 확인 (배송완료인 경우)
        if delivery_status == '배송완료':
            days_passed = self._calculate_days_since_delivery(order)
            if days_passed is not None:
                if days_passed > self.refund_period_days:
                    if not is_defective:  # 불량품은 기간 제한 없음
                        refundable = False
                        reasons.append(f"배송완료 후 {self.refund_period_days}일이 경과했습니다. (경과일: {days_passed}일)")
                else:
                    reasons.append(f"환불 가능 기간 내입니다. (경과일: {days_passed}일)")
        
        # 3. 개인위생용품 확인
        product_name = order.get('product_name', '')
        category = order.get('category', '')
        category_check = self.policy_tool.execute(
            query_type='category_check',
            product_name=product_name,
            category=category
        )
        
        if category_check['is_hygiene_product']:
            if not is_defective:  # 불량품이 아닌 개인위생용품
                refundable = False
                reasons.append("개인위생용품은 불량품이 아닌 경우 환불이 불가능합니다.")
            else:
                reasons.append("개인위생용품이지만 불량품이므로 환불 가능합니다.")
        
        # 4. 사용 흔적 확인
        if has_usage_trace and not is_defective:
            reasons.append("사용 흔적이 있는 경우 추가 수수료가 발생할 수 있습니다.")
        
        # 5. 수수료 정보
        if refundable and delivery_status in ['배송중', '배송완료']:
            fee_applies = status_policy['policy'].get('fee', False)
            if fee_applies:
                reasons.append("환불 수수료가 적용됩니다.")
        
        return {
            "success": True,
            "refundable": refundable,
            "reasons": reasons,
            "details": {
                "order_id": order.get('order_id'),
                "product_name": product_name,
                "category": category,
                "delivery_status": delivery_status,
                "is_hygiene_product": category_check.get('is_hygiene_product', False),
                "is_defective": is_defective,
                "has_usage_trace": has_usage_trace,
                "days_since_delivery": self._calculate_days_since_delivery(order),
                "price": order.get('price', 0)  # 가격 정보 추가
            }
        }
    
    def _calculate_days_since_delivery(self, order: Dict[str, Any]) -> Optional[int]:
        """배송 완료 후 경과 일수 계산"""
        if order.get('delivery_status') != '배송완료':
            return None
        
        delivery_date = order.get('delivery_date')
        if not delivery_date:
            return None
        
        try:
            delivery_datetime = datetime.strptime(delivery_date, '%Y-%m-%d')
            # 현재 시간 기준 (실제로는 2025-08-22 기준으로 계산)
            current_date = datetime(2025, 8, 22)
            days_passed = (current_date - delivery_datetime).days
            return days_passed
        except ValueError:
            return None
    
    def batch_validate(self, order_ids: list) -> Dict[str, Any]:
        """여러 주문의 환불 가능 여부 일괄 검증"""
        results = []
        
        for order_id in order_ids:
            validation = self.execute(order_id=order_id)
            results.append({
                "order_id": order_id,
                **validation
            })
        
        refundable_count = sum(1 for r in results if r.get('refundable', False))
        
        return {
            "success": True,
            "total_orders": len(order_ids),
            "refundable_count": refundable_count,
            "non_refundable_count": len(order_ids) - refundable_count,
            "results": results
        }
