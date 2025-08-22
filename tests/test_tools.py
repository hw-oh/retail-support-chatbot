"""
툴 테스트 스크립트
"""
from tools import (
    CatalogTool, OrderHistoryTool, RefundPolicyTool,
    RefundCalculatorTool, RefundValidatorTool, RefundProcessorTool
)


def test_catalog_tool():
    """카탈로그 툴 테스트"""
    print("\n=== 카탈로그 툴 테스트 ===")
    catalog = CatalogTool()
    
    # 제품명으로 검색
    result = catalog.execute(product_name="나이키")
    print(f"나이키 검색 결과: {result['count']}개")
    if result['products']:
        print(f"첫 번째 제품: {result['products'][0]['product_name']} - {result['products'][0]['price']:,}원")
    
    # 카테고리로 검색
    result = catalog.execute(category="화장품")
    print(f"화장품 카테고리: {result['count']}개")


def test_order_history_tool():
    """주문 이력 툴 테스트"""
    print("\n=== 주문 이력 툴 테스트 ===")
    order_history = OrderHistoryTool()
    
    # 주문번호로 검색
    result = order_history.execute(order_id="ORD20241201001")
    if result['success']:
        order = result['orders'][0]
        print(f"주문 찾음: {order['product_name']} - {order['delivery_status']}")
    
    # 배송완료 후 경과일 계산
    days = order_history.calculate_days_since_delivery("ORD20241201001")
    print(f"배송완료 후 경과일: {days}일")


def test_refund_policy_tool():
    """환불 정책 툴 테스트"""
    print("\n=== 환불 정책 툴 테스트 ===")
    policy = RefundPolicyTool()
    
    # 기본 규칙 조회
    result = policy.execute(query_type='basic_rules')
    print(f"환불 가능 기간: {result['policy']['refund_period']}일")
    print(f"환불 수수료율: {result['policy']['refund_fee_rate']*100}%")
    
    # 개인위생용품 체크
    result = policy.execute(query_type='category_check', product_name='네이처리퍼블릭 알로에젤')
    print(f"알로에젤 개인위생용품 여부: {result['is_hygiene_product']}")


def test_refund_calculator_tool():
    """환불 계산기 툴 테스트"""
    print("\n=== 환불 계산기 툴 테스트 ===")
    calculator = RefundCalculatorTool()
    
    # 배송완료 상품 환불 계산
    result = calculator.execute(
        product_price=89000,
        delivery_status="배송완료"
    )
    print(f"상품가격: {result['product_price']:,}원")
    print(f"환불수수료: {result['refund_fee']:,}원")
    print(f"배송비: {result['shipping_fee']:,}원")
    print(f"최종 환불금액: {result['refund_amount']:,}원")


def test_refund_validator_tool():
    """환불 검증 툴 테스트"""
    print("\n=== 환불 검증 툴 테스트 ===")
    validator = RefundValidatorTool()
    
    # 7일 이내 주문 테스트 (배송완료)
    result = validator.execute(order_id="ORD20241209009")  # H&M 청바지, 12월 12일 배송완료
    print(f"주문번호 ORD20241209009 (H&M 청바지) 환불 가능: {result['refundable']}")
    print(f"사유: {result['reasons']}")
    
    # 개인위생용품 환불 시도
    result = validator.execute(order_id="ORD20241202002")
    print(f"\n주문번호 ORD20241202002 (알로에젤) 환불 가능: {result['refundable']}")
    print(f"사유: {result['reasons']}")
    
    # 배송 전 취소 테스트
    result = validator.execute(order_id="ORD20241213013")  # 아디다스 후드티, 결제완료 상태
    print(f"\n주문번호 ORD20241213013 (아디다스 후드티, 결제완료) 환불 가능: {result['refundable']}")
    print(f"사유: {result['reasons']}")


def test_refund_processor_tool():
    """환불 처리 툴 테스트"""
    print("\n=== 환불 처리 툴 테스트 ===")
    processor = RefundProcessorTool()
    
    # 환불 처리 (7일 이내 주문으로 변경)
    result = processor.execute(
        order_id="ORD20241209009",  # H&M 청바지
        reason="사이즈가 맞지 않음",
        customer_note="한 사이즈 작아요"
    )
    
    if result['success']:
        print(f"환불 처리 성공! 환불 ID: {result['refund_id']}")
        details = result['refund_details']
        print(f"환불 금액: {details['refund_amount']:,}원")
        print(f"다음 단계:")
        for step in result['next_steps']:
            print(f"  - {step}")
    else:
        print(f"환불 처리 실패: {result['message']}")
        if 'reasons' in result:
            print(f"사유: {result['reasons']}")


def main():
    """모든 툴 테스트 실행"""
    test_catalog_tool()
    test_order_history_tool()
    test_refund_policy_tool()
    test_refund_calculator_tool()
    test_refund_validator_tool()
    test_refund_processor_tool()


if __name__ == "__main__":
    main()
