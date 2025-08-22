"""
환불 처리 실행 툴 (시뮬레이션)
"""
from typing import Any, Dict, Optional
from datetime import datetime
import random
from .base import BaseTool
from .refund_validator_tool import RefundValidatorTool
from .refund_calculator_tool import RefundCalculatorTool


class RefundProcessorTool(BaseTool):
    """환불을 실제로 처리하는 툴 (시뮬레이션)"""
    
    def __init__(self, validator_tool: Optional[RefundValidatorTool] = None,
                 calculator_tool: Optional[RefundCalculatorTool] = None):
        super().__init__(
            name="RefundProcessorTool",
            description="환불 요청을 처리합니다 (시뮬레이션)"
        )
        self.validator_tool = validator_tool or RefundValidatorTool()
        self.calculator_tool = calculator_tool or RefundCalculatorTool()
        self.processed_refunds = []  # 처리된 환불 내역 저장
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        환불 처리 실행
        
        Args:
            order_id: 주문 번호
            reason: 환불 사유
            is_defective: 불량품 여부
            customer_note: 고객 메모
        
        Returns:
            처리 결과
        """
        order_id = kwargs.get('order_id')
        reason = kwargs.get('reason', '고객 변심')
        is_defective = kwargs.get('is_defective', False)
        customer_note = kwargs.get('customer_note', '')
        
        if not order_id:
            return {
                "success": False,
                "message": "주문번호가 필요합니다.",
                "refund_id": None
            }
        
        # 1. 환불 가능 여부 검증
        validation = self.validator_tool.execute(
            order_id=order_id,
            is_defective=is_defective
        )
        
        if not validation['refundable']:
            return {
                "success": False,
                "message": "환불이 불가능합니다.",
                "reasons": validation['reasons'],
                "refund_id": None
            }
        
        # 2. 주문 정보 가져오기
        order_details = validation['details']
        
        # 3. 환불 금액 계산
        # 주문 정보에서 가격 가져오기 (validation details에 없을 수도 있음)
        order = self.validator_tool.order_tool.get_order_by_id(order_id)
        product_price = order.get('price', 0) if order else order_details.get('price', 0)
        
        calculation = self.calculator_tool.execute(
            product_price=product_price,
            delivery_status=order_details.get('delivery_status', ''),
            is_defective=is_defective
        )
        
        if not calculation['success']:
            return {
                "success": False,
                "message": "환불 금액 계산에 실패했습니다.",
                "refund_id": None
            }
        
        # 4. 환불 처리 (시뮬레이션)
        refund_id = self._process_refund(
            order_id=order_id,
            order_details=order_details,
            calculation=calculation,
            reason=reason,
            customer_note=customer_note
        )
        
        # 5. 처리 결과 반환
        return {
            "success": True,
            "message": "환불이 성공적으로 처리되었습니다.",
            "refund_id": refund_id,
            "refund_details": {
                "order_id": order_id,
                "product_name": order_details.get('product_name'),
                "original_price": calculation['product_price'],
                "refund_fee": calculation['refund_fee'],
                "shipping_fee": calculation['shipping_fee'],
                "refund_amount": calculation['refund_amount'],
                "processing_date": datetime(2025, 8, 22, 14, 30, 0).strftime('%Y-%m-%d %H:%M:%S'),
                "reason": reason,
                "status": "처리완료"
            },
            "next_steps": self._get_next_steps(order_details.get('delivery_status'))
        }
    
    def _process_refund(self, order_id: str, order_details: Dict[str, Any],
                       calculation: Dict[str, Any], reason: str, 
                       customer_note: str) -> str:
        """환불 처리 시뮬레이션"""
        
        # 환불 ID 생성 (2025년 8월 22일 기준)
        current_time = datetime(2025, 8, 22, 14, 30, 0)  # 오후 2시 30분으로 고정
        refund_id = f"REF{current_time.strftime('%Y%m%d%H%M%S')}{order_id[-3:]}"
        
        # 환불 내역 저장
        refund_record = {
            "refund_id": refund_id,
            "order_id": order_id,
            "product_name": order_details.get('product_name'),
            "original_price": calculation['product_price'],
            "refund_amount": calculation['refund_amount'],
            "refund_fee": calculation['refund_fee'],
            "shipping_fee": calculation['shipping_fee'],
            "reason": reason,
            "customer_note": customer_note,
            "processing_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "status": "처리완료"
        }
        
        self.processed_refunds.append(refund_record)
        
        return refund_id
    
    def _get_next_steps(self, delivery_status: str) -> list:
        """배송 상태에 따른 다음 단계 안내"""
        steps = []
        
        if delivery_status in ['주문접수', '결제완료', '상품준비중']:
            steps.append("주문이 즉시 취소되었습니다.")
            steps.append("환불 금액은 영업일 기준 3-5일 내에 원래 결제 수단으로 입금됩니다.")
        
        elif delivery_status == '배송중':
            steps.append("배송 중인 상품의 회수를 요청했습니다.")
            steps.append("상품이 회수되면 환불이 진행됩니다.")
            steps.append("환불 금액은 상품 확인 후 영업일 기준 3-5일 내에 입금됩니다.")
        
        elif delivery_status == '배송완료':
            steps.append("택배사를 통해 상품 회수가 진행됩니다.")
            steps.append("회수 신청 후 1-2일 내에 택배 기사가 방문할 예정입니다.")
            steps.append("상품을 반송할 수 있도록 포장해 주세요.")
            steps.append("상품 확인 후 영업일 기준 3-5일 내에 환불금이 입금됩니다.")
        
        return steps
    
    def get_refund_status(self, refund_id: str) -> Dict[str, Any]:
        """환불 처리 상태 조회"""
        for refund in self.processed_refunds:
            if refund['refund_id'] == refund_id:
                return {
                    "success": True,
                    "refund": refund
                }
        
        return {
            "success": False,
            "message": f"환불 ID {refund_id}를 찾을 수 없습니다."
        }
    
    def get_all_refunds(self) -> Dict[str, Any]:
        """모든 환불 내역 조회"""
        return {
            "success": True,
            "total_refunds": len(self.processed_refunds),
            "refunds": self.processed_refunds
        }
