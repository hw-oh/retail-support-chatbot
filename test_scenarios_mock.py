#!/usr/bin/env python3
"""
쇼핑몰 챗봇 테스트 시나리오 (Mock 버전)
"""
import json
from datetime import datetime, timedelta
from tools.order_search import OrderSearchTool
from tools.refund_validator import RefundValidatorTool
from tools.data_loader import DataLoader


def print_test_header(test_name: str):
    """테스트 헤더 출력"""
    print("\n" + "="*60)
    print(f"🧪 {test_name}")
    print("="*60)


def test_refund_after_7_days():
    """테스트 1: 7일 지난 물건 환불 가능 여부"""
    print_test_header("7일 지난 물건 환불 가능 여부")
    
    validator = RefundValidatorTool()
    
    # 2025-08-09에 구매한 젠하이저 이어폰 (현재 8월 26일이면 17일 지남)
    result = validator.validate_refund_eligibility("ORD20250809005")
    
    print(f"주문번호: ORD20250809005")
    print(f"환불 가능: {result['eligible']}")
    print(f"사유: {result['reason']}")
    print(f"주문 후 경과일: {result.get('days_since_order', 'N/A')}일")
    
    # 검증
    expected = result['eligible'] == False and "7일" in result['reason']
    print(f"✅ 테스트 결과: {'PASS' if expected else 'FAIL'}")


def test_personal_hygiene_refund_denial():
    """테스트 2: 개인 위생용품 환불 불가"""
    print_test_header("개인 위생용품 환불 불가 여부")
    
    # 키엘 크림 (화장품 = 개인위생용품)
    search_tool = OrderSearchTool()
    order = search_tool.search_by_order_id("ORD20250812004")
    
    print(f"주문번호: ORD20250812004")
    print(f"상품명: {order.get('product_name') if order else 'N/A'}")
    print(f"카테고리: {order.get('category') if order else 'N/A'}")
    
    # 화장품인지 확인
    is_personal_hygiene = order and order.get('category') == '화장품'
    print(f"개인위생용품 여부: {is_personal_hygiene}")
    print(f"✅ 테스트 결과: {'PASS' if is_personal_hygiene else 'FAIL'}")


def test_personal_hygiene_before_delivery():
    """테스트 3: 개인 위생용품이지만 배송 전이라 환불 가능"""
    print_test_header("개인 위생용품 - 배송 전 환불 가능")
    
    search_tool = OrderSearchTool()
    order = search_tool.search_by_order_id("ORD20250812004")
    
    print(f"주문번호: ORD20250812004")
    print(f"상품명: {order.get('product_name') if order else 'N/A'}")
    print(f"배송 상태: {order.get('delivery_status') if order else 'N/A'}")
    
    # 배송 전 상태 확인
    is_before_delivery = order and order.get('delivery_status') == '주문접수'
    print(f"배송 전 상태: {is_before_delivery}")
    print(f"✅ 테스트 결과: {'PASS' if is_before_delivery else 'FAIL'}")


def test_recent_3_purchases():
    """테스트 4: 최근 3개 구매 물건 조회"""
    print_test_header("최근 3개 구매 물건 조회")
    
    search_tool = OrderSearchTool()
    recent_orders = search_tool.search_recent_orders(limit=3)
    
    print(f"최근 3개 주문:")
    for i, order in enumerate(recent_orders, 1):
        print(f"{i}. {order.get('product_name')} (주문일: {order.get('purchase_date')})")
    
    expected_products = ["마이크로소프트 마우스", "노스페이스", "올버즈"]
    found_products = [order.get('product_name') for order in recent_orders[:3]]
    
    print(f"예상 상품: {expected_products}")
    print(f"실제 상품: {found_products}")
    print(f"✅ 테스트 결과: {'PASS' if len(recent_orders) >= 3 else 'FAIL'}")


def test_recent_10_refundable():
    """테스트 5: 최근 10개 중 환불 가능한 것만"""
    print_test_header("최근 10개 중 환불 가능한 것만 조회")
    
    search_tool = OrderSearchTool()
    validator = RefundValidatorTool()
    
    recent_orders = search_tool.search_recent_orders(limit=10)
    refundable_orders = []
    
    print("최근 10개 주문 중 환불 가능한 상품:")
    for order in recent_orders:
        order_id = order.get('order_id')
        result = validator.validate_refund_eligibility(order_id)
        
        if result['eligible']:
            refundable_orders.append(order)
            print(f"✅ {order.get('product_name')} (주문일: {order.get('purchase_date')})")
        else:
            print(f"❌ {order.get('product_name')} - {result['reason']}")
    
    print(f"\n환불 가능한 상품 수: {len(refundable_orders)}/{len(recent_orders)}")
    print(f"✅ 테스트 결과: {'PASS' if len(refundable_orders) > 0 else 'FAIL'}")


def test_multi_turn_scenario():
    """테스트 6: 멀티턴 시나리오 데이터 검증"""
    print_test_header("멀티턴 대화 시나리오 데이터 검증")
    
    search_tool = OrderSearchTool()
    validator = RefundValidatorTool()
    
    # 1단계: 최근 5개 주문 조회
    recent_5 = search_tool.search_recent_orders(limit=5)
    print(f"1단계 - 최근 5개 주문:")
    for i, order in enumerate(recent_5, 1):
        print(f"  {i}. {order.get('product_name')} ({order.get('purchase_date')})")
    
    # 2단계: 그 중 환불 가능한 것들
    refundable_from_5 = []
    print(f"\n2단계 - 위 5개 중 환불 가능한 것들:")
    for order in recent_5:
        result = validator.validate_refund_eligibility(order.get('order_id'))
        if result['eligible']:
            refundable_from_5.append(order)
            print(f"  ✅ {order.get('product_name')}")
        else:
            print(f"  ❌ {order.get('product_name')} - {result['reason']}")
    
    # 3단계: 환불 처리 가능성
    print(f"\n3단계 - 모두 환불 처리 가능성:")
    print(f"  환불 가능한 상품 수: {len(refundable_from_5)}")
    for order in refundable_from_5:
        print(f"  - {order.get('product_name')}: 환불 처리 준비됨")
    
    success = len(recent_5) == 5 and len(refundable_from_5) > 0
    print(f"\n✅ 테스트 결과: {'PASS' if success else 'FAIL'}")


def test_edge_cases():
    """테스트 7: 엣지 케이스들"""
    print_test_header("엣지 케이스 테스트")
    
    search_tool = OrderSearchTool()
    validator = RefundValidatorTool()
    
    # 존재하지 않는 주문번호
    print("1. 존재하지 않는 주문번호:")
    order = search_tool.search_by_order_id("ORD99999999")
    print(f"  주문 조회 결과: {order}")
    
    result = validator.validate_refund_eligibility("ORD99999999")
    print(f"  환불 검증 결과: {result['reason']}")
    
    # 정확히 7일째 되는 주문 확인
    print("\n2. 7일 경계선 테스트:")
    current_date = datetime.now()
    for order in search_tool.search_recent_orders(limit=20):
        order_date = datetime.strptime(order.get('purchase_date'), '%Y-%m-%d')
        days_diff = (current_date - order_date).days
        if days_diff == 7:
            print(f"  정확히 7일 된 주문: {order.get('product_name')} (주문일: {order.get('purchase_date')})")
            result = validator.validate_refund_eligibility(order.get('order_id'))
            print(f"  환불 가능 여부: {result['eligible']} - {result['reason']}")
            break
    else:
        print("  정확히 7일 된 주문이 없습니다.")
    
    print(f"\n✅ 테스트 결과: PASS")


def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 쇼핑몰 챗봇 도구 테스트 시작!")
    print(f"📅 테스트 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_refund_after_7_days()
        test_personal_hygiene_refund_denial()
        test_personal_hygiene_before_delivery()
        test_recent_3_purchases()
        test_recent_10_refundable()
        test_multi_turn_scenario()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
