"""
Multi-turn 대화 데모 - Shopping Mall Agent
"""
import asyncio
from agents.shopping_mall_agent import ShoppingMallAgent


async def demo_shopping_mall_agent():
    """Shopping Mall Agent 데모 (Multi-turn 대화 지원)"""
    print("=== Shopping Mall Agent Demo (Multi-turn Support) ===\n")
    
    agent = ShoppingMallAgent()
    session_id = None
    
    # 시나리오: 구매 내역 -> 환불 가능 확인 -> 다른 제품 환불
    conversations = [
        "일주일 이내 구매한 제품 보여줘",
        "그 중에 뭘 환불할 수 있어?", 
        "다른 물건을 환불하고 싶어"
    ]
    
    for user_input in conversations:
        print(f"사용자: {user_input}")
        
        result = agent.process_message(user_input, session_id)
        session_id = result["session_id"]
        
        print(f"봇: {result['response']}")
        print(f"대화 단계: {result['dialog_state']['phase']}")
        print(f"활성 컨텍스트: {result['dialog_state']['active_context']}")
        print(f"캐시된 결과: {result['dialog_state']['cached_results']}")
        print("-" * 50)


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_shopping_mall_agent())
