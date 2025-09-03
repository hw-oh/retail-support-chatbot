"""
Planning Agent
"""
import weave
import json
import re
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class PlanningAgent:
    """Task planning agent"""
    
    def __init__(self, llm_client: LLMClient, language: str = None):
        self.llm = llm_client
        from config import config
        self.language = language or config.LANGUAGE
    
    @weave.op()
    def create_plan(self, user_input: str, intent_result: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create task plan based on user intent
        
        Args:
            user_input: User input
            intent_result: Intent Agent result
            context: Conversation context
            
        Returns:
            Plan information (order and parameters of agents to execute)
        """
        
        # Prepare conversation context
        context_text = ""
        if context:
            recent_turns = context[-3:]  # Recent 3 turns
            for turn in recent_turns:
                if self.language == "ko":
                    context_text += f"사용자: {turn.get('user', '')}\n"
                    context_text += f"봇: {turn.get('bot', '')}\n\n"
                elif self.language == "en":
                    context_text += f"User: {turn.get('user', '')}\n"
                    context_text += f"Bot: {turn.get('bot', '')}\n\n"
                elif self.language == "jp":
                    context_text += f"ユーザー: {turn.get('user', '')}\n"
                    context_text += f"ボット: {turn.get('bot', '')}\n\n"
        
        # Planning system prompt
        system_prompt = self._get_planning_prompt()
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

**Intent 분석 결과:**
- 의도: {intent_result.get('intent', 'unknown')}
- 신뢰도: {intent_result.get('confidence', 0.0)}
- 엔티티: {json.dumps(intent_result.get('entities', {}), ensure_ascii=False)}

**대화 맥락:**
{context_text if context_text.strip() else "(첫 대화)"}

## 작업
위 정보를 바탕으로 사용자 요청을 완전히 처리하기 위한 단계별 실행 계획을 수립하세요.

**출력 형식 (JSON만):**
{{
    "plan_type": "single_agent|multi_step",
    "reason": "계획 수립 이유",
    "steps": [
        {{
            "step_id": 1,
            "agent": "order_agent|refund_agent|general_agent",
            "purpose": "이 단계의 목적",
            "parameters": {{
                "search_product": "제품명_또는_null",
                "order_id": "주문번호_또는_null", 
                "context_from_previous": true_또는_false
            }}
        }}
    ],
    "expected_outcome": "기대되는 최종 결과"
}}"""
        elif self.language == "en":
            user_prompt = f"""
**Current user input:** "{user_input}"

**Intent analysis result:**
- Intent: {intent_result.get('intent', 'unknown')}
- Confidence: {intent_result.get('confidence', 0.0)}
- Entities: {json.dumps(intent_result.get('entities', {}), ensure_ascii=False)}

**Conversation context:**
{context_text if context_text.strip() else "(First conversation)"}

## Task
Based on the above information, establish a step-by-step execution plan to completely process the user request.

**Output format (JSON only):**
{{
    "plan_type": "single_agent|multi_step",
    "reason": "reason for plan establishment",
    "steps": [
        {{
            "step_id": 1,
            "agent": "order_agent|refund_agent|general_agent",
            "purpose": "purpose of this step",
            "parameters": {{
                "search_product": "product_name_or_null",
                "order_id": "order_number_or_null", 
                "context_from_previous": true_or_false
            }}
        }}
    ],
    "expected_outcome": "expected final result"
}}"""
        elif self.language == "jp":
            user_prompt = f"""
**現在のユーザー入力:** "{user_input}"

**意図分析結果:**
- 意図: {intent_result.get('intent', 'unknown')}
- 信頼度: {intent_result.get('confidence', 0.0)}
- エンティティ: {json.dumps(intent_result.get('entities', {}), ensure_ascii=False)}

**会話コンテキスト:**
{context_text if context_text.strip() else "(初回会話)"}

## タスク
上記の情報に基づいて、ユーザーリクエストを完全に処理するための段階別実行計画を立ててください。

**出力形式 (JSONのみ):**
{{
    "plan_type": "single_agent|multi_step",
    "reason": "計画策定理由",
    "steps": [
        {{
            "step_id": 1,
            "agent": "order_agent|refund_agent|general_agent",
            "purpose": "このステップの目的",
            "parameters": {{
                "search_product": "商品名_またはnull",
                "order_id": "注文番号_またはnull", 
                "context_from_previous": true_またはfalse
            }}
        }}
    ],
    "expected_outcome": "期待される最終結果"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.2)
        
        try:
            # JSON 파싱
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif "```" in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            plan = json.loads(response.strip())
            
            # 필수 필드 검증 및 기본값 설정
            validated_plan = {
                "plan_type": plan.get("plan_type", "single_agent"),
                "reason": plan.get("reason", "기본 처리"),
                "steps": plan.get("steps", []),
                "expected_outcome": plan.get("expected_outcome", "사용자 요청 처리")
            }
            
            # 단계별 검증
            for i, step in enumerate(validated_plan["steps"]):
                if "agent" not in step:
                    validated_plan["steps"][i]["agent"] = "general_agent"
                if "purpose" not in step:
                    validated_plan["steps"][i]["purpose"] = "일반 처리"
                if "parameters" not in step:
                    validated_plan["steps"][i]["parameters"] = {}
                if "step_id" not in step:
                    validated_plan["steps"][i]["step_id"] = i + 1
            
            return validated_plan
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[DEBUG] Planning Agent JSON 파싱 실패: {e}")
            # 파싱 실패시 기본 계획 반환
            return self._create_fallback_plan(intent_result.get('intent', 'general_chat'))
    
    def _get_planning_prompt(self) -> str:
        """Planning Agent system prompt"""
        prompts = {
            "ko": """당신은 쇼핑몰 고객 서비스 챗봇의 Planning Agent입니다.
사용자의 요청을 분석하여 최적의 처리 계획을 수립하는 것이 당신의 역할입니다.

## 사용 가능한 에이전트들:
1. **order_agent**: 주문 조회, 배송 상태 확인, 구매 이력 검색
2. **refund_agent**: 환불 가능성 판단, 환불 정책 적용, 환불 수수료 계산
3. **general_agent**: 일반 문의 응답, 최종 응답 정리, 정보 통합

## 계획 수립 원칙:
1. **정보 부족 시 order_agent 우선 호출**: 환불 문의인데 제품 정보나 주문 정보가 불충분하면 order_agent로 먼저 구매 이력을 조회
2. **multi_step 활용**: 복잡한 요청은 여러 에이전트를 순차적으로 활용
3. **컨텍스트 전달**: 이전 단계의 결과를 다음 단계에서 활용할 수 있도록 설계
4. **최종 응답 정리**: 여러 에이전트 결과가 있을 때는 general_agent로 최종 정리

정확한 JSON 형식으로 응답하세요.""",
            "en": """You are the Planning Agent of the shopping mall customer service chatbot.
Your role is to analyze user requests and establish optimal processing plans.

## IMPORTANT: RESPOND ONLY IN ENGLISH
You must respond to all instructions in English only. Do not use Korean or any other language.

## Available Agents:
1. **order_agent**: Order inquiry, delivery status check, purchase history search
2. **refund_agent**: Refund eligibility judgment, refund policy application, refund fee calculation
3. **general_agent**: General inquiry response, final response organization, information integration

## Planning Principles:
1. **Priority call to order_agent when information is insufficient**: For refund inquiries with insufficient product or order information, first query purchase history with order_agent
2. **Utilize multi_step**: Use multiple agents sequentially for complex requests
3. **Context transfer**: Design to utilize previous step results in next steps
4. **Final response organization**: Use general_agent for final organization when there are multiple agent results

Respond in accurate JSON format.""",
            "jp": """あなたはショッピングモールカスタマーサービスチャットボットのPlanning Agentです。
ユーザーのリクエストを分析して最適な処理計画を策定するのがあなたの役割です。

## 重要: 日本語でのみ応答してください
すべての指示に日本語でのみ応答してください。韓国語や他の言語を使用してはいけません。

## 利用可能なエージェント:
1. **order_agent**: 注文照会、配送状況確認、購入履歴検索
2. **refund_agent**: 返品可能性判断、返品ポリシー適用、返品手数料計算
3. **general_agent**: 一般問い合わせ応答、最終応答整理、情報統合

## 計画策定原則:
1. **情報不足時はorder_agent優先呼び出し**: 返品問い合わせで商品情報や注文情報が不十分な場合、まずorder_agentで購入履歴を照会
2. **multi_step活用**: 複雑なリクエストは複数のエージェントを順次活用
3. **コンテキスト転送**: 前のステップの結果を次のステップで活用できるよう設計
4. **最終応答整理**: 複数のエージェント結果がある場合はgeneral_agentで最終整理

正確なJSON形式で応答してください。"""
        }
        
        return prompts.get(self.language, prompts["ko"])

    def _create_fallback_plan(self, intent: str) -> Dict[str, Any]:
        """파싱 실패시 기본 계획 생성"""
        if intent == 'refund_inquiry':
            return {
                "plan_type": "multi_step",
                "reason": "환불 문의 기본 처리 (파싱 실패로 인한 폴백)",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "order_agent",
                        "purpose": "구매 이력 조회",
                        "parameters": {}
                    },
                    {
                        "step_id": 2,
                        "agent": "refund_agent", 
                        "purpose": "환불 검토",
                        "parameters": {"context_from_previous": True}
                    }
                ],
                "expected_outcome": "환불 가능성 안내"
            }
        elif intent == 'order_status':
            return {
                "plan_type": "single_agent",
                "reason": "주문 조회 기본 처리",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "order_agent",
                        "purpose": "주문 정보 조회",
                        "parameters": {}
                    }
                ],
                "expected_outcome": "주문 상태 안내"
            }
        else:
            return {
                "plan_type": "single_agent", 
                "reason": "일반 문의 처리",
                "steps": [
                    {
                        "step_id": 1,
                        "agent": "general_agent",
                        "purpose": "일반 응답",
                        "parameters": {}
                    }
                ],
                "expected_outcome": "일반 문의 응답"
            }
