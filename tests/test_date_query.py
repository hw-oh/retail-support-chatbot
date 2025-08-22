"""
날짜 기반 주문 조회 테스트
"""
from agents import ShoppingMallAgent


def test_date_queries():
    """다양한 날짜 기반 쿼리 테스트"""
    print("🧪 날짜 기반 주문 조회 테스트")
    print("="*60)
    
    agent = ShoppingMallAgent()
    
    test_queries = [
        "지난 일주일 동안 구매한 내용을 보여줘",
        "최근 일주일간 주문 내역 확인해줘",
        "최근 3일 동안 산 것들 보여줘",
        "어제 주문한 거 있나요?",
        "지난주에 뭐 샀는지 알려줘",
        "이번 주 구매 내역 보여줘"
    ]
    
    for query in test_queries:
        print(f"\n👤 사용자: {query}")
        
        response = agent.process_message(query)
        
        # 실행된 계획 확인
        if response.get("plan"):
            for step in response["plan"]:
                if step["status"] == "completed":
                    print(f"   📋 실행: {step['description']}")
                    if step.get("params"):
                        params = step["params"]
                        if "start_date" in params:
                            print(f"      기간: {params.get('start_date')} ~ {params.get('end_date')}")
        
        # 응답에서 찾은 주문 개수 확인
        response_text = response["response"]
        if "개의 주문을 찾았습니다" in response_text:
            import re
            match = re.search(r'총 (\d+)개의 주문을 찾았습니다', response_text)
            if match:
                count = match.group(1)
                print(f"   ✅ 결과: {count}개 주문 발견")
        elif "주문 정보를 찾을 수 없습니다" in response_text:
            print(f"   ❌ 결과: 주문 없음")
        else:
            # 응답의 첫 100자만 출력
            print(f"   🤖 응답: {response_text[:100]}...")


def test_specific_period():
    """특정 기간 조회 상세 테스트"""
    print("\n\n📌 특정 기간 조회 상세 테스트")
    print("="*60)
    
    agent = ShoppingMallAgent()
    
    # 최근 7일 조회
    query = "지난 일주일 동안 구매한 내용을 보여줘"
    print(f"\n👤 사용자: {query}")
    
    response = agent.process_message(query)
    
    print("\n🤖 챗봇 응답:")
    print(response["response"])
    
    # 실제로 날짜 범위가 맞는지 확인
    print("\n📊 분석:")
    if "ORD202412" in response["response"]:
        print("✅ 12월 주문이 포함되어 있음")
    if "배송완료" in response["response"]:
        print("✅ 배송 상태 정보 포함")
    
    # 날짜별 주문 개수 카운트
    import re
    dates = re.findall(r'주문일: (2024-\d{2}-\d{2})', response["response"])
    if dates:
        print(f"\n📅 발견된 주문 날짜들:")
        for date in set(dates):
            count = dates.count(date)
            print(f"   - {date}: {count}건")


def main():
    test_date_queries()
    test_specific_period()


if __name__ == "__main__":
    main()
