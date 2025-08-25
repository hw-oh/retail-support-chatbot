"""
환불 가능 여부 검증 툴 - LLM 기반
"""
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import json
from .base import BaseTool
from .order_history_tool import OrderHistoryTool
from .refund_policy_tool import RefundPolicyTool
from agents.base import get_llm_client
import config


class RefundValidatorTool(BaseTool):
    """환불 가능 여부를 검증하는 툴 - LLM 기반"""
    
    def __init__(self, order_tool: Optional[OrderHistoryTool] = None, 
                 policy_tool: Optional[RefundPolicyTool] = None):
        super().__init__(
            name="RefundValidatorTool",
            description="주문의 환불 가능 여부를 검증합니다"
        )
        self.order_tool = order_tool or OrderHistoryTool()
        self.policy_tool = policy_tool or RefundPolicyTool()
        self.refund_period_days = 7
        self.llm = get_llm_client()
    
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
        """환불 가능 여부 상세 검증 - LLM 기반"""
        
        # 환불 정책 조회
        status_policy = self.policy_tool.execute(
            query_type='status_policy', 
            delivery_status=order.get('delivery_status', '')
        )
        
        category_check = self.policy_tool.execute(
            query_type='category_check',
            product_name=order.get('product_name', ''),
            category=order.get('category', '')
        )
        
        days_since_delivery = self._calculate_days_since_delivery(order)
        
        # LLM에 전달할 정보 구성
        validation_context = {
            "current_date": config.CURRENT_DATE,
            "order_info": {
                "order_id": order.get('order_id'),
                "product_name": order.get('product_name', ''),
                "category": order.get('category', ''),
                "delivery_status": order.get('delivery_status', ''),
                "delivery_date": order.get('delivery_date'),
                "price": order.get('price', 0),
                "days_since_delivery": days_since_delivery
            },
            "product_conditions": {
                "is_defective": is_defective,
                "has_usage_trace": has_usage_trace,
                "is_hygiene_product": category_check.get('is_hygiene_product', False)
            },
            "refund_policies": {
                "refund_period_days": self.refund_period_days,
                "status_policy": status_policy.get('policy', {}),
                "hygiene_product_policy": "개인위생용품은 불량품이 아닌 경우 환불 불가",
                "defective_product_policy": "불량품은 기간 제한 없이 환불 가능",
                "usage_trace_policy": "사용 흔적이 있는 경우 추가 수수료 적용 가능"
            }
        }
        
        # LLM에 검증 요청
        messages = [
            {
                "role": "system",
                "content": """You are a refund validation expert for a Korean e-commerce platform.
Based on the provided order information and refund policies, determine if a refund is possible.

Consider all relevant factors:
1. Delivery status and whether refunds are allowed in that status
2. Time elapsed since delivery (if applicable)
3. Product category restrictions (e.g., hygiene products)
4. Product condition (defective, usage traces)
5. Applicable fees

Provide clear reasoning for your decision in Korean."""
            },
            {
                "role": "user",
                "content": f"""Please validate if the following order is eligible for refund:

{json.dumps(validation_context, ensure_ascii=False, indent=2)}

Output in JSON format:
{{
    "refundable": boolean,
    "reasons": ["list of reasons in Korean"],
    "fee_applies": boolean,
    "fee_percentage": number (0-100)
}}"""
            }
        ]
        
        try:
            # LLM 응답 schema
            schema = {
                "type": "object",
                "properties": {
                    "refundable": {"type": "boolean"},
                    "reasons": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "fee_applies": {"type": "boolean"},
                    "fee_percentage": {"type": "number", "minimum": 0, "maximum": 100}
                },
                "required": ["refundable", "reasons"]
            }
            
            result = self.llm.generate_json(messages, schema=schema)
            
            return {
                "success": True,
                "refundable": result.get("refundable", False),
                "reasons": result.get("reasons", []),
                "details": {
                    "order_id": order.get('order_id'),
                    "product_name": order.get('product_name', ''),
                    "category": order.get('category', ''),
                    "delivery_status": order.get('delivery_status', ''),
                    "is_hygiene_product": category_check.get('is_hygiene_product', False),
                    "is_defective": is_defective,
                    "has_usage_trace": has_usage_trace,
                    "days_since_delivery": days_since_delivery,
                    "price": order.get('price', 0),
                    "fee_applies": result.get("fee_applies", False),
                    "fee_percentage": result.get("fee_percentage", 0)
                }
            }
            
        except Exception as e:
            print(f"LLM validation error: {e}")
            # Error fallback
            return {
                "success": False,
                "refundable": False,
                "reasons": ["환불 가능 여부 검증 중 오류가 발생했습니다."],
                "details": {
                    "order_id": order.get('order_id'),
                    "error": str(e)
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
