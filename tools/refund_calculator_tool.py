"""
환불 수수료 계산 툴
"""
from typing import Any, Dict
from .base import BaseTool


class RefundCalculatorTool(BaseTool):
    """환불 수수료를 계산하는 툴"""
    
    def __init__(self):
        super().__init__(
            name="RefundCalculatorTool",
            description="환불 수수료와 최종 환불 금액을 계산합니다"
        )
        self.fee_rate = 0.1  # 10%
        self.minimum_fee = 2000  # 최소 수수료 2,000원
        self.shipping_fee = 3000  # 기본 배송비 (편도)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        환불 수수료 계산 실행
        
        Args:
            product_price: 상품 가격
            delivery_status: 배송 상태
            is_defective: 불량품 여부
            include_shipping: 배송비 포함 여부
        
        Returns:
            계산 결과
        """
        product_price = kwargs.get('product_price', 0)
        delivery_status = kwargs.get('delivery_status', '')
        is_defective = kwargs.get('is_defective', False)
        include_shipping = kwargs.get('include_shipping', True)
        
        if product_price <= 0:
            return {
                "success": False,
                "message": "상품 가격이 올바르지 않습니다."
            }
        
        # 배송 전 상태는 수수료 없음
        if delivery_status in ['주문접수', '결제완료', '상품준비중']:
            return {
                "success": True,
                "product_price": product_price,
                "refund_fee": 0,
                "shipping_fee": 0,
                "total_deduction": 0,
                "refund_amount": product_price,
                "fee_details": "배송 전 취소는 수수료가 없습니다."
            }
        
        # 환불 수수료 계산
        calculated_fee = int(product_price * self.fee_rate)
        refund_fee = max(calculated_fee, self.minimum_fee)
        
        # 배송비 계산
        shipping_fee = 0
        if include_shipping and delivery_status in ['배송중', '배송완료']:
            # 배송완료는 왕복 배송비, 배송중은 편도 배송비
            if delivery_status == '배송완료':
                shipping_fee = self.shipping_fee * 2  # 왕복
            else:
                shipping_fee = self.shipping_fee  # 편도
        
        # 총 차감액
        total_deduction = refund_fee + shipping_fee
        
        # 최종 환불 금액
        refund_amount = product_price - total_deduction
        
        # 상세 설명
        fee_details = self._generate_fee_details(
            product_price, refund_fee, shipping_fee, 
            calculated_fee < self.minimum_fee, delivery_status
        )
        
        return {
            "success": True,
            "product_price": product_price,
            "refund_fee": refund_fee,
            "shipping_fee": shipping_fee,
            "total_deduction": total_deduction,
            "refund_amount": refund_amount,
            "fee_details": fee_details
        }
    
    def _generate_fee_details(self, price: int, fee: int, shipping: int, 
                            is_minimum_applied: bool, status: str) -> str:
        """수수료 상세 설명 생성"""
        details = []
        
        # 환불 수수료 설명
        if fee > 0:
            if is_minimum_applied:
                details.append(f"환불 수수료: {fee:,}원 (최소 수수료 적용)")
            else:
                details.append(f"환불 수수료: {fee:,}원 (상품가격의 10%)")
        
        # 배송비 설명
        if shipping > 0:
            if status == '배송완료':
                details.append(f"배송비: {shipping:,}원 (왕복 배송비)")
            else:
                details.append(f"배송비: {shipping:,}원 (편도 배송비)")
        
        # 최종 설명
        if details:
            details.append(f"총 차감액: {fee + shipping:,}원")
            details.append(f"최종 환불 금액: {price - fee - shipping:,}원")
        
        return " / ".join(details) if details else "수수료가 없습니다."
    
    def calculate_bulk_refund(self, orders: list) -> Dict[str, Any]:
        """여러 주문의 환불 금액 일괄 계산"""
        results = []
        total_refund = 0
        total_fee = 0
        
        for order in orders:
            calc_result = self.execute(
                product_price=order.get('price', 0),
                delivery_status=order.get('delivery_status', ''),
                is_defective=order.get('is_defective', False)
            )
            
            if calc_result['success']:
                results.append({
                    "order_id": order.get('order_id'),
                    "product_name": order.get('product_name'),
                    **calc_result
                })
                total_refund += calc_result['refund_amount']
                total_fee += calc_result['total_deduction']
        
        return {
            "success": True,
            "individual_results": results,
            "total_original_price": sum(order.get('price', 0) for order in orders),
            "total_fee": total_fee,
            "total_refund_amount": total_refund
        }
