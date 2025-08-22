"""
LLM-powered Shopping Mall Chatbot Demo
"""
import os
from agents import ShoppingMallAgent
from config import config
import json


def print_divider():
    print("\n" + "="*70)


def print_response_details(response):
    """Print detailed response information"""
    print("\n🤖 챗봇 응답:")
    print("-" * 70)
    print(response["response"])
    
    # Intent and confidence
    print(f"\n📊 분석 결과:")
    print(f"  - 의도: {response.get('intent', 'unknown')}")
    print(f"  - 신뢰도: {response.get('confidence', 0):.2f}")
    
    # Entities
    if response.get("entities"):
        print(f"  - 추출된 정보: {json.dumps(response['entities'], ensure_ascii=False)}")
    
    # Tool executions
    if response.get("plan"):
        print(f"\n🔧 실행된 도구:")
        for step in response["plan"]:
            if step.get("status") == "completed":
                print(f"  ✅ {step['tool_name']}: {step['description']}")
    
    # Confirmation needed
    if response.get("needs_confirmation"):
        print("\n⚠️  확인이 필요합니다!")


def run_interactive_demo():
    """Run interactive demo"""
    print("🛍️ LLM 기반 쇼핑몰 챗봇 데모")
    print("="*70)
    
    # Check configuration
    if not config.validate():
        print("\n⚠️  OpenAI API key가 설정되지 않았습니다.")
        print("Mock 모드로 실행됩니다. (제한된 기능)")
        use_mock = input("\n계속하시겠습니까? (y/n): ")
        if use_mock.lower() != 'y':
            return
    
    print(f"\n📅 현재 날짜: {config.CURRENT_DATE}")
    print(f"🤖 사용 모델: {config.OPENAI_MODEL}")
    
    print("\n💡 사용 가능한 기능:")
    print("1. 자연스러운 대화로 의도 파악")
    print("2. 문맥을 고려한 멀티턴 대화")
    print("3. 자동 계획 수립 및 실행")
    print("4. 상황에 맞는 응답 생성")
    
    print("\n💡 예제 문장:")
    print("- 최근에 산 마우스가 고장났어요. 환불 받을 수 있나요?")
    print("- 지난 주에 주문한 것들 보여주세요")
    print("- 5만원 이하 화장품 추천해주세요")
    print("- 어제 산 노트북 파우치 배송 상태 알려주세요")
    
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
                
            # Process message
            response = agent.process_message(user_input, session_id)
            session_id = response["session_id"]
            
            # Print response details
            print_divider()
            print_response_details(response)
            print_divider()
            
        except KeyboardInterrupt:
            print("\n\n종료합니다. 감사합니다! 👋")
            break
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {str(e)}")
            print("다시 시도해주세요.")


def run_test_scenarios():
    """Run predefined test scenarios"""
    print("🧪 LLM 기반 챗봇 시나리오 테스트")
    print("="*70)
    
    agent = ShoppingMallAgent()
    
    scenarios = [
        {
            "name": "복잡한 환불 문의",
            "conversation": [
                "안녕하세요. 도움이 필요해요.",
                "최근에 산 마우스가 이상해요. 클릭이 안돼요.",
                "마이크로소프트 마우스예요. 3일 전에 샀어요.",
                "네, 환불하고 싶어요."
            ]
        },
        {
            "name": "날짜 기반 조회",
            "conversation": [
                "지난 일주일 동안 뭘 샀는지 궁금해요",
                "그 중에 전자제품만 보여주세요"
            ]
        },
        {
            "name": "제품 추천",
            "conversation": [
                "생일 선물로 줄 화장품을 찾고 있어요",
                "3만원에서 5만원 사이로 추천해주세요"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n\n📌 시나리오: {scenario['name']}")
        print("-" * 50)
        
        session_id = None
        for i, message in enumerate(scenario['conversation']):
            print(f"\n👤 사용자: {message}")
            
            response = agent.process_message(message, session_id)
            session_id = response["session_id"]
            
            print(f"🤖 챗봇: {response['response'][:200]}...")
            
            if response.get("intent") and response.get("confidence") is not None:
                print(f"   [의도: {response['intent']}, 신뢰도: {response['confidence']:.2f}]")
            elif response.get("intent"):
                print(f"   [의도: {response['intent']}]")
    
    print("\n\n✅ 모든 시나리오 테스트 완료!")


def main():
    """Main function"""
    print("LLM 기반 쇼핑몰 챗봇 데모")
    print("1. 대화형 데모")
    print("2. 시나리오 테스트")
    
    choice = input("\n선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        run_interactive_demo()
    elif choice == "2":
        run_test_scenarios()
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    # Set OpenAI API key for testing (remove in production)
    # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    main()
