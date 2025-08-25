#!/usr/bin/env python3
"""
쇼핑몰 챗봇 테스트 시나리오
"""
import weave
from datetime import datetime, timedelta
from simple_chatbot import SimplifiedChatbot


def print_test_header(test_name: str):
    """테스트 헤더 출력"""
    print("\n" + "="*60)
    print(f"🧪 {test_name}")
    print("="*60)


def print_test_result(user_input: str, response: str, expected_keywords: list = None):
    """테스트 결과 출력"""
    print(f"\n👤 사용자: {user_input}")
    print(f"🤖 봇: {response}")
    
    if expected_keywords:
        found_keywords = [kw for kw in expected_keywords if kw.lower() in response.lower()]
        print(f"✅ 검증 키워드: {found_keywords}/{expected_keywords}")


def test_refund_after_7_days():
    """테스트 1: 7일 지난 물건 환불 가능 여부"""
    print_test_header("7일 지난 물건 환불 가능 여부")
    
    chatbot = SimplifiedChatbot()
    
    # 2025-08-09에 구매한 젠하이저 이어폰 (오늘이 8월 19일이면 10일 지남)
    user_input = "ORD20250809005 주문번호로 환불하고 싶어요"
    response = chatbot.chat(user_input)
    
    print_test_result(user_input, response, ["7일", "환불 불가", "기간"])


def test_personal_hygiene_refund_denial():
    """테스트 2: 개인 위생용품 환불 불가"""
    print_test_header("개인 위생용품 환불 불가 여부")
    
    chatbot = SimplifiedChatbot()
    
    # 키엘 크림 (화장품 = 개인위생용품)
    user_input = "ORD20250812004 키엘 크림을 환불하고 싶어요"
    response = chatbot.chat(user_input)
    
    print_test_result(user_input, response, ["개인위생용품", "환불 불가", "화장품"])


def test_personal_hygiene_before_delivery():
    """테스트 3: 개인 위생용품이지만 배송 전이라 환불 가능"""
    print_test_header("개인 위생용품 - 배송 전 환불 가능")
    
    chatbot = SimplifiedChatbot()
    
    # 키엘 크림 - 주문접수 상태
    user_input = "아직 배송되지 않은 키엘 크림을 취소하고 싶어요"
    response = chatbot.chat(user_input)
    
    print_test_result(user_input, response, ["취소 가능", "배송 전", "무료"])


def test_recent_3_purchases():
    """테스트 4: 최근 3개 구매 물건 조회"""
    print_test_header("최근 3개 구매 물건 조회")
    
    chatbot = SimplifiedChatbot()
    
    user_input = "최근 구매한 물건 3개를 보여주세요"
    response = chatbot.chat(user_input)
    
    print_test_result(user_input, response, ["마이크로소프트 마우스", "노스페이스", "올버즈"])


def test_recent_10_refundable():
    """테스트 5: 최근 10개 중 환불 가능한 것만"""
    print_test_header("최근 10개 중 환불 가능한 것만 조회")
    
    chatbot = SimplifiedChatbot()
    
    user_input = "최근 구매한 물건 10개 중에서 환불 가능한 것만 알려주세요"
    response = chatbot.chat(user_input)
    
    print_test_result(user_input, response, ["환불 가능", "7일 이내", "마이크로소프트"])


def test_multi_turn_conversation():
    """테스트 6: 멀티턴 대화"""
    print_test_header("멀티턴 대화 테스트")
    
    chatbot = SimplifiedChatbot()
    
    # 턴 1: 최근 구매 물건 5개 요청
    user_input1 = "최근 구매한 물건 5개를 보여주세요"
    response1 = chatbot.chat(user_input1)
    print_test_result(user_input1, response1, ["5개", "구매"])
    
    # 턴 2: 그 중 환불 가능한 것 요청
    user_input2 = "그 중 환불 가능한 것을 알려주세요"
    response2 = chatbot.chat(user_input2)
    print_test_result(user_input2, response2, ["환불 가능", "그 중"])
    
    # 턴 3: 모두 환불 요청
    user_input3 = "모두 환불해주세요"
    response3 = chatbot.chat(user_input3)
    print_test_result(user_input3, response3, ["환불", "처리"])


def test_edge_cases():
    """테스트 7: 엣지 케이스들"""
    print_test_header("엣지 케이스 테스트")
    
    chatbot = SimplifiedChatbot()
    
    # 존재하지 않는 주문번호
    user_input = "ORD99999999 주문을 환불하고 싶어요"
    response = chatbot.chat(user_input)
    print_test_result(user_input, response, ["주문을 찾을 수 없습니다", "존재하지 않"])


def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 쇼핑몰 챗봇 테스트 시작!")
    print(f"📅 테스트 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Weave 초기화
    weave.init('chatbot-test-scenarios')
    
    try:
        test_refund_after_7_days()
        test_personal_hygiene_refund_denial()
        test_personal_hygiene_before_delivery()
        test_recent_3_purchases()
        test_recent_10_refundable()
        test_multi_turn_conversation()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")


if __name__ == "__main__":
    run_all_tests()
