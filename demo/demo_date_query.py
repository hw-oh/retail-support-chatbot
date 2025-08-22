"""
날짜 기반 조회 대화형 데모
"""
from agents import ShoppingMallAgent


def main():
    print("🛍️ 쇼핑몰 챗봇 - 날짜 기반 조회 데모")
    print("="*60)
    print("💡 예제 문장:")
    print("- 지난 일주일 동안 구매한 내용을 보여줘")
    print("- 최근 3일간 주문 내역 보여줘")
    print("- 어제 뭐 샀는지 알려줘")
    print("- 지난달에 구매한 것들 보여줘")
    print("- 12월 10일부터 15일까지 주문 내역 확인해줘")
    print("\n종료하려면 'quit' 또는 '종료'를 입력하세요.\n")
    
    agent = ShoppingMallAgent()
    session_id = None
    
    while True:
        try:
            user_input = input("\n👤 사용자: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료', '그만']:
                print("\n감사합니다. 좋은 하루 되세요! 👋")
                break
                
            if not user_input:
                continue
                
            response = agent.process_message(user_input, session_id)
            session_id = response["session_id"]
            
            print("\n🤖 챗봇:")
            print(response["response"])
            
            if response.get("plan"):
                print("\n📋 실행된 작업:")
                for step in response["plan"]:
                    if step["status"] == "completed":
                        print(f"  ✅ {step['description']}")
                        if "start_date" in step.get("params", {}):
                            params = step["params"]
                            print(f"     기간: {params['start_date']} ~ {params['end_date']}")
                            
        except KeyboardInterrupt:
            print("\n\n종료합니다. 감사합니다! 👋")
            break
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
