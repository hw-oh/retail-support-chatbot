"""
간소화된 멀티턴 쇼핑몰 챗봇
- Intent 분석 → 적절한 에이전트 라우팅 → 응답 생성
- While 루프로 멀티턴 대화 지원
- 지속적인 컨텍스트 관리
"""
import weave
from typing import List, Dict, Any

# 에이전트 import
from agents import LLMClient, IntentAgent, OrderAgent, RefundAgent, GeneralAgent


# 이제 에이전트들은 별도 파일에서 import됩니다


class SimplifiedChatbot:
    """간소화된 멀티턴 챗봇"""
    
    def __init__(self):
        # LLM 클라이언트
        self.llm = LLMClient()
        
        # 1. Intent 분석 에이전트
        self.intent_agent = IntentAgent(self.llm)
        
        # 2. 도메인별 에이전트들
        self.agents = {
            'order_status': OrderAgent(self.llm),
            'refund_inquiry': RefundAgent(self.llm), 
            'general_chat': GeneralAgent(self.llm),
            'product_inquiry': GeneralAgent(self.llm),  # 임시로 일반 에이전트 사용
            'clarification': None  # 동적 처리
        }
        
        # 3. 대화 컨텍스트 (멀티턴용)
        self.conversation_context: List[Dict[str, Any]] = []
    
    @weave.op()
    def chat(self, user_input: str) -> str:
        """단일 턴 처리"""
        
        # 1. Intent 분석
        intent_result = self.intent_agent.classify(user_input, self.conversation_context)
        intent = intent_result.get('intent', 'general_chat')
        entities = intent_result.get('entities', {})
        
        # 2. 적절한 에이전트에 라우팅
        if intent == 'clarification':
            # 이전 컨텍스트 기반으로 적절한 에이전트 선택
            if entities.get('refund_reference'):
                agent = self.agents['refund_inquiry']
            else:
                agent = self.agents['order_status']
        else:
            agent = self.agents.get(intent, self.agents['general_chat'])
        
        # 3. 에이전트 실행
        agent_response = agent.handle(user_input, self.conversation_context)
        
        # 4. 응답 처리 (refund agent는 구조화된 응답 반환)
        if intent == 'refund_inquiry' and isinstance(agent_response, dict):
            # 자연스러운 대화체 응답 우선 사용, 없으면 기존 user_response 사용
            response = agent_response.get('conversational_response', 
                                        agent_response.get('user_response', str(agent_response)))
            # 컨텍스트에는 전체 구조화된 응답 저장
            self.conversation_context.append({
                'user': user_input,
                'bot': response,
                'agent_data': agent_response,  # 구조화된 데이터 저장
                'intent': intent,
                'entities': entities
            })
        else:
            response = str(agent_response)
            # 4. 컨텍스트 업데이트
            self.conversation_context.append({
                'user': user_input,
                'bot': response,
                'intent': intent,
                'entities': entities
            })
        
        return response
    
    def chat_loop(self):
        """멀티턴 대화 루프"""
        print("\n🛍️ 쇼핑몰 챗봇에 오신걸 환영합니다!")
        print("주문 조회와 환불 문의를 도와드립니다.")
        print("'종료'를 입력하면 대화를 마칩니다.\n")
        
        with weave.thread() as thread_ctx:
            print(f"Thread ID: {thread_ctx.thread_id}")
        
            while True:
                try:
                    user_input = input("고객님: ").strip()
                    
                    if user_input.lower() in ['종료', 'exit', 'quit']:
                        print("대화를 종료합니다. 감사합니다! 👋")
                        break
                    
                    if not user_input:
                        continue
                    
                    # 챗봇 응답
                    response = self.chat(user_input)
                    print(f"봇: {response}\n")
                    
                except KeyboardInterrupt:
                    print("\n\n대화를 종료합니다. 감사합니다! 👋")
                    break
                except Exception as e:
                    print(f"오류 발생: {e}")


def main():
    """메인 실행 함수"""
    # Weave 초기화
    weave.init('wandb-korea/retail-chatbot-dev')
    
    # 챗봇 생성 및 실행
    chatbot = SimplifiedChatbot()
    chatbot.chat_loop()


if __name__ == "__main__":
    main()
