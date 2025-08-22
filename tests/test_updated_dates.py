"""
날짜 업데이트 후 테스트
"""
from agents import ShoppingMallAgent
import json


def check_recent_orders():
    """최근 주문 확인"""
    print("📅 최근 주문 확인 (2025년 8월 22일 기준)")
    print("="*60)
    
    with open('data/purchase_history.json', 'r', encoding='utf-8') as f:
        purchases = json.load(f)
    
    print("\n최근 10개 주문:")
    for i, purchase in enumerate(purchases[:10]):
        status = purchase['delivery_status']
        date_info = f"주문: {purchase['purchase_date']}"
        if purchase.get('delivery_date'):
            date_info += f", 배송: {purchase['delivery_date']}"
        
        print(f"{i+1}. {purchase['product_name']} ({purchase['order_id']})")
        print(f"   {date_info}, 상태: {status}")
    

def test_date_queries():
    """날짜 기반 조회 테스트"""
    print("\n\n🧪 날짜 기반 조회 테스트")
    print("="*60)
    
    agent = ShoppingMallAgent()
    
    queries = [
        ("오늘 주문한 것 있어?", "오늘"),
        ("어제 뭐 샀어?", "어제"), 
        ("최근 3일간 구매 내역 보여줘", "3일"),
        ("지난 일주일 동안 구매한 내용 알려줘", "7일"),
        ("이번 달에 산 것들 보여줘", "이번 달")
    ]
    
    for query, desc in queries:
        print(f"\n👤 {desc} 조회: \"{query}\"")
        
        response = agent.process_message(query)
        
        # 결과 요약
        if "개의 주문을 찾았습니다" in response["response"]:
            import re
            match = re.search(r'총 (\d+)개의 주문을 찾았습니다', response["response"])
            if match:
                count = match.group(1)
                print(f"   ✅ {count}개 주문 발견")
                
                # 주문 목록 일부 표시
                orders = re.findall(r'(\d+)\. (.+?) \(ORD(\d+)\)', response["response"])
                for idx, (num, product, order_num) in enumerate(orders[:3]):
                    print(f"      - {product}")
                if len(orders) > 3:
                    print(f"      ... 외 {len(orders)-3}개")
        else:
            print("   ❌ 주문 없음")


def test_refund_scenario():
    """환불 시나리오 테스트"""
    print("\n\n🔄 환불 시나리오 테스트")
    print("="*60)
    
    agent = ShoppingMallAgent()
    
    # 최근 주문 중 하나로 환불 테스트
    print("\n1️⃣ 최근 주문 환불 테스트")
    
    # 첫 번째: 최근 주문 조회
    response1 = agent.process_message("최근 3일간 주문한 것 중에 환불 가능한 거 있어?")
    session_id = response1["session_id"]
    
    print("👤 사용자: 최근 3일간 주문한 것 중에 환불 가능한 거 있어?")
    print(f"🤖 챗봇: {response1['response'][:200]}...")
    
    # 두 번째: 특정 주문 환불 요청
    response2 = agent.process_message("ORD20250819001 환불하고 싶어요", session_id)
    
    print("\n👤 사용자: ORD20250819001 환불하고 싶어요")
    print(f"🤖 챗봇: {response2['response'][:200]}...")
    
    # 환불 가능 여부 확인
    if "환불이 가능합니다" in response2['response']:
        print("\n✅ 환불 가능 확인!")
    elif "환불이 불가능합니다" in response2['response']:
        print("\n❌ 환불 불가 - 사유 확인 필요")


def main():
    print("🛍️ 쇼핑몰 챗봇 - 날짜 업데이트 테스트")
    print("현재 날짜: 2025년 8월 22일")
    print("="*60)
    
    check_recent_orders()
    test_date_queries()
    test_refund_scenario()
    
    print("\n\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
