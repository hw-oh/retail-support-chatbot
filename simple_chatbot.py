"""
간소화된 멀티턴 쇼핑몰 챗봇
- Intent 분석 → 적절한 에이전트 라우팅 → 응답 생성
- While 루프로 멀티턴 대화 지원
- 지속적인 컨텍스트 관리
"""
import weave
from typing import List, Dict, Any

# 에이전트 import
from agents import LLMClient, IntentAgent, PlanningAgent, OrderAgent, RefundAgent, GeneralAgent
from config import config


# 이제 에이전트들은 별도 파일에서 import됩니다


class SimplifiedChatbot:
    """간소화된 멀티턴 챗봇"""
    
    def __init__(self):
        # 1. Intent 분석 에이전트 (경량 모델)
        intent_llm = LLMClient(model=config.INTENT_AGENT_MODEL)
        self.intent_agent = IntentAgent(intent_llm)
        
        # 2. Planning 에이전트 (경량 모델)
        planning_llm = LLMClient(model=config.PLANNING_AGENT_MODEL)
        self.planning_agent = PlanningAgent(planning_llm)
        
        # 3. 도메인별 에이전트들 (각각 적절한 모델 사용)
        order_llm = LLMClient(model=config.ORDER_AGENT_MODEL)
        refund_llm = LLMClient(model=config.REFUND_AGENT_MODEL)
        general_llm = LLMClient(model=config.GENERAL_AGENT_MODEL)
        
        self.agents = {
            'order_agent': OrderAgent(order_llm),
            'refund_agent': RefundAgent(refund_llm), 
            'general_agent': GeneralAgent(general_llm)
        }
        
        # 4. 대화 컨텍스트 (멀티턴용)
        self.conversation_context: List[Dict[str, Any]] = []
    
    @weave.op()
    def chat(self, user_input: str, order_info: Dict[str, Any] = None) -> str:
        """Planning Agent 기반 멀티 스텝 처리"""
        
        # 1. Intent 분석
        intent_result = self.intent_agent.classify(user_input, self.conversation_context)
        intent = intent_result.get('intent', 'general_chat')
        entities = intent_result.get('entities', {})
        
        # 2. Planning Agent가 실행 계획 수립
        plan = self.planning_agent.create_plan(user_input, intent_result, self.conversation_context)
        
        print(f"[DEBUG] 실행 계획: {plan['plan_type']} - {plan['reason']}")
        
        # 3. 계획에 따라 에이전트들을 순차 실행
        step_results = []
        for step in plan['steps']:
            agent_name = step['agent']
            agent = self.agents.get(agent_name)
            
            if not agent:
                print(f"[WARNING] 에이전트 '{agent_name}'를 찾을 수 없습니다.")
                continue
            
            print(f"[DEBUG] Step {step['step_id']}: {agent_name} - {step['purpose']}")
            
            # 이전 스텝의 결과를 컨텍스트에 반영
            if step['parameters'].get('context_from_previous') and step_results:
                # 이전 결과를 임시 컨텍스트에 추가
                temp_context = self.conversation_context.copy()
                prev_result = step_results[-1]
                temp_context.append({
                    'user': f"[이전 단계 결과] {step['purpose']}",
                    'bot': str(prev_result),
                    'step_result': True
                })
                current_context = temp_context
            else:
                current_context = self.conversation_context
            
            # 에이전트 실행
            try:
                # OrderAgent인 경우 order_info 전달
                if agent_name == 'order_agent' and hasattr(agent, 'handle_with_order_info'):
                    step_result = agent.handle_with_order_info(user_input, current_context, order_info)
                else:
                    step_result = agent.handle(user_input, current_context)
                step_results.append(step_result)
                print(f"[DEBUG] Step {step['step_id']} 완료")
            except Exception as e:
                print(f"[ERROR] Step {step['step_id']} 실행 중 오류: {e}")
                step_results.append(f"오류 발생: {str(e)}")
        
        # 4. 최종 응답 처리
        final_response = self._process_final_response(plan, step_results, intent)
        
        # 5. 컨텍스트 업데이트 (planning 정보 포함)
        self.conversation_context.append({
            'user': user_input,
            'bot': final_response,
            'intent': intent,
            'entities': entities,
            'plan': plan,
            'step_results': step_results
        })
        
        return final_response
    
    def _process_final_response(self, plan: Dict[str, Any], step_results: List[Any], intent: str) -> str:
        """단계별 결과를 최종 응답으로 처리"""
        
        if not step_results:
            return "죄송합니다. 요청을 처리하는 중 문제가 발생했습니다."
        
        # single_agent인 경우 마지막 결과만 반환
        if plan['plan_type'] == 'single_agent':
            result = step_results[-1]
            if isinstance(result, dict):
                return result.get('conversational_response', 
                               result.get('user_response', str(result)))
            return str(result)
        
        # multi_step인 경우 마지막 결과를 우선 반환 (보통 general_agent나 refund_agent)
        last_result = step_results[-1]
        if isinstance(last_result, dict):
            return last_result.get('conversational_response',
                                 last_result.get('user_response', str(last_result)))
        
        # 마지막 결과가 문자열이면 그대로 반환
        return str(last_result)
    
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
