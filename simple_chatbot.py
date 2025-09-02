"""
간소화된 멀티턴 쇼핑몰 챗봇
- Intent 분석 → 적절한 에이전트 라우팅 → 응답 생성
- While 루프로 멀티턴 대화 지원
- 지속적인 컨텍스트 관리
"""
import weave
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# 에이전트 import
from agents import LLMClient, IntentAgent, PlanningAgent, OrderAgent, RefundAgent, GeneralAgent
from config import config


@dataclass
class AgentOutput:
    """에이전트 출력 정보를 구조화"""
    agent_name: str
    step_id: int
    raw_output: Any
    structured_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class ConversationTurn:
    """단일 대화 턴의 완전한 정보"""
    user_input: str
    bot_response: str
    intent: str
    entities: Dict[str, Any]
    plan: Optional[Dict[str, Any]] = None
    agent_outputs: List[AgentOutput] = None
    
    def __post_init__(self):
        if self.agent_outputs is None:
            self.agent_outputs = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextManager:
    """대화 컨텍스트 관리자 - 채팅 내용과 구조화된 데이터 분리"""
    
    def __init__(self):
        self.conversation_history: List[ConversationTurn] = []
    
    def add_turn(self, turn: ConversationTurn):
        """새로운 대화 턴 추가"""
        self.conversation_history.append(turn)
    
    def get_recent_turns(self, count: int = 3) -> List[ConversationTurn]:
        """최근 N개 턴 반환"""
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def get_legacy_context(self) -> List[Dict[str, Any]]:
        """기존 방식의 채팅 컨텍스트 반환 (호환성용)"""
        legacy_context = []
        for turn in self.get_recent_turns():
            legacy_context.append({
                'user': turn.user_input,
                'bot': turn.bot_response,
                'intent': turn.intent,
                'entities': turn.entities
            })
        return legacy_context
    
    def get_structured_context_for_llm(self) -> str:
        """LLM 입력용 구조화된 컨텍스트 생성"""
        recent_turns = self.get_recent_turns()
        if not recent_turns:
            return "(첫 대화)"
        
        context_parts = []
        for i, turn in enumerate(recent_turns, 1):
            context_parts.append(f"## 대화 {i}")
            context_parts.append(f"사용자: {turn.user_input}")
            context_parts.append(f"봇 응답: {turn.bot_response}")
            
            # 의도 및 엔티티 정보
            if turn.intent != 'general_chat':
                context_parts.append(f"분석된 의도: {turn.intent}")
                if turn.entities:
                    context_parts.append(f"추출된 정보: {json.dumps(turn.entities, ensure_ascii=False)}")
            
            # 에이전트별 구조화된 데이터
            if turn.agent_outputs:
                for output in turn.agent_outputs:
                    if output.structured_data:
                        context_parts.append(f"## {output.agent_name} 결과")
                        context_parts.append(json.dumps(output.structured_data, ensure_ascii=False, indent=2))
            
            context_parts.append("")  # 빈 줄로 구분
        
        return "\n".join(context_parts)
    
    def get_latest_agent_output(self, agent_name: str) -> Optional[AgentOutput]:
        """특정 에이전트의 최신 출력 반환"""
        for turn in reversed(self.conversation_history):
            for output in turn.agent_outputs:
                if output.agent_name == agent_name:
                    return output
        return None


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
        
        # 4. 대화 컨텍스트 관리자
        self.context_manager = ContextManager()
    
    @weave.op()
    def chat(self, user_input: str, order_info: Dict[str, Any] = None) -> str:
        """Planning Agent 기반 멀티 스텝 처리"""
        
        # 1. Intent 분석 (레거시 컨텍스트 사용)
        legacy_context = self.context_manager.get_legacy_context()
        intent_result = self.intent_agent.classify(user_input, legacy_context)
        intent = intent_result.get('intent', 'general_chat')
        entities = intent_result.get('entities', {})
        
        # 2. Planning Agent가 실행 계획 수립
        plan = self.planning_agent.create_plan(user_input, intent_result, legacy_context)
        
        # 3. 계획에 따라 에이전트들을 순차 실행
        agent_outputs = []
        for step in plan['steps']:
            agent_name = step['agent']
            agent = self.agents.get(agent_name)
            
            if not agent:
                print(f"[WARNING] 에이전트 '{agent_name}'를 찾을 수 없습니다.")
                continue
            
            # 구조화된 컨텍스트 생성
            structured_context = self.context_manager.get_structured_context_for_llm()
            
            # 이전 스텝의 결과를 구조화된 컨텍스트에 추가
            if step['parameters'].get('context_from_previous') and agent_outputs:
                prev_output = agent_outputs[-1]
                if prev_output.structured_data:
                    structured_context += f"\n\n## 이전 단계 결과\n{json.dumps(prev_output.structured_data, ensure_ascii=False, indent=2)}"
            
            # 에이전트 실행
            try:
                # OrderAgent인 경우 order_info 전달
                if agent_name == 'order_agent' and hasattr(agent, 'handle_with_structured_context'):
                    raw_result = agent.handle_with_structured_context(user_input, structured_context, order_info)
                elif hasattr(agent, 'handle_with_structured_context'):
                    raw_result = agent.handle_with_structured_context(user_input, structured_context)
                else:
                    # 레거시 방식으로 폴백
                    raw_result = self._call_agent_legacy(agent, agent_name, user_input, order_info)
                
                # 에이전트 출력을 구조화
                agent_output = self._create_agent_output(agent_name, step['step_id'], raw_result)
                agent_outputs.append(agent_output)
                
            except Exception as e:
                print(f"[ERROR] Step {step['step_id']} 실행 중 오류: {e}")
                error_output = AgentOutput(
                    agent_name=agent_name,
                    step_id=step['step_id'],
                    raw_output=f"오류 발생: {str(e)}",
                    structured_data={"error": str(e), "agent_type": agent_name}
                )
                agent_outputs.append(error_output)
        
        # 4. 최종 응답 처리
        final_response = self._process_final_response_v2(plan, agent_outputs, intent)
        
        # 5. 구조화된 컨텍스트로 저장
        conversation_turn = ConversationTurn(
            user_input=user_input,
            bot_response=final_response,
            intent=intent,
            entities=entities,
            plan=plan,
            agent_outputs=agent_outputs
        )
        self.context_manager.add_turn(conversation_turn)
        
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
    
    def _call_agent_legacy(self, agent, agent_name: str, user_input: str, order_info: Dict = None):
        """레거시 방식으로 에이전트 호출"""
        legacy_context = self.context_manager.get_legacy_context()
        
        if agent_name == 'order_agent' and hasattr(agent, 'handle_with_order_info'):
            return agent.handle_with_order_info(user_input, legacy_context, order_info)
        else:
            return agent.handle(user_input, legacy_context)
    
    def _create_agent_output(self, agent_name: str, step_id: int, raw_result: Any) -> AgentOutput:
        """에이전트 출력을 구조화된 형태로 변환"""
        structured_data = None
        
        if agent_name == 'order_agent':
            # Order Agent 출력 구조화
            structured_data = {
                "agent_type": "order_search",
                "response_summary": str(raw_result),
                "found_orders": True if "주문" in str(raw_result) else False,
                "search_timestamp": "current",
                "time_analysis_included": True if "일 전" in str(raw_result) or "환불" in str(raw_result) else False,
                "contains_refund_status": True if "환불" in str(raw_result) else False
            }
        
        elif agent_name == 'refund_agent':
            # Refund Agent 출력 구조화
            if isinstance(raw_result, dict):
                structured_data = {
                    "agent_type": "refund_decision",
                    "refund_possible": raw_result.get('refund_possible'),
                    "refund_fee": raw_result.get('refund_fee', 0),
                    "total_refund_amount": raw_result.get('total_refund_amount', 0),
                    "reason": raw_result.get('reason', ''),
                    "policy_applied": raw_result.get('policy_applied', []),
                    "decision_timestamp": "current"
                }
            else:
                structured_data = {
                    "agent_type": "refund_decision",
                    "response_summary": str(raw_result)[:200] + "..." if len(str(raw_result)) > 200 else str(raw_result)
                }
        
        elif agent_name == 'planning_agent':
            # Planning Agent 출력 구조화
            if isinstance(raw_result, dict):
                structured_data = {
                    "agent_type": "planning",
                    "plan_type": raw_result.get('plan_type'),
                    "steps_count": len(raw_result.get('steps', [])),
                    "reason": raw_result.get('reason'),
                    "expected_outcome": raw_result.get('expected_outcome')
                }
        
        elif agent_name == 'general_agent':
            # General Agent 출력 구조화
            structured_data = {
                "agent_type": "general_response",
                "response_summary": str(raw_result)[:200] + "..." if len(str(raw_result)) > 200 else str(raw_result),
                "response_timestamp": "current"
            }
        
        else:
            # 기본 구조화
            structured_data = {
                "agent_type": agent_name,
                "response_summary": str(raw_result)[:200] + "..." if len(str(raw_result)) > 200 else str(raw_result)
            }
        
        return AgentOutput(
            agent_name=agent_name,
            step_id=step_id,
            raw_output=raw_result,
            structured_data=structured_data
        )
    
    def _process_final_response_v2(self, plan: Dict[str, Any], agent_outputs: List[AgentOutput], intent: str) -> str:
        """구조화된 에이전트 출력을 최종 응답으로 처리"""
        
        if not agent_outputs:
            return "죄송합니다. 요청을 처리하는 중 문제가 발생했습니다."
        
        # single_agent인 경우 마지막 결과만 반환
        if plan['plan_type'] == 'single_agent':
            last_output = agent_outputs[-1]
            if hasattr(last_output.raw_output, 'get'):
                return last_output.raw_output.get('conversational_response', 
                                                last_output.raw_output.get('user_response', str(last_output.raw_output)))
            return str(last_output.raw_output)
        
        # multi_step인 경우 마지막 결과를 우선 반환
        last_output = agent_outputs[-1]
        if hasattr(last_output.raw_output, 'get'):
            return last_output.raw_output.get('conversational_response',
                                            last_output.raw_output.get('user_response', str(last_output.raw_output)))
        
        return str(last_output.raw_output)
    
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
