"""
Refund Management Agent
"""
import weave
import json
import re
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class RefundAgent:
    """환불 처리 에이전트"""
    
    def __init__(self, llm_client: LLMClient, language: str = None):
        self.llm = llm_client
        from config import config
        from prompts.weave_prompts import WeavePromptManager
        self.language = language or config.LANGUAGE
        # Create dedicated prompt manager for this agent
        self.prompt_manager = WeavePromptManager()
        self.prompt_manager.set_language(self.language)
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """환불 문의 처리"""
        
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
        
        # Get prompt from Weave (refund policy is already included)
        system_prompt = self.prompt_manager.get_refund_agent_prompt()
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 작업 지시
위 대화 맥락을 고려하여 사용자의 환불 요청을 처리해주세요. 
응답은 다음 형식의 JSON으로 제공해주세요:

{{
    "refund_possible": true/false,
    "refund_fee": 숫자 (환불 수수료, 없으면 0),
    "total_refund_amount": 숫자 (실제 환불 금액),
    "reason": "환불 가능/불가능한 상세 이유",
    "user_response": "사용자에게 보여줄 친절한 응답",
    "policy_applied": ["적용된 정책 목록"]
}}

정확한 JSON 형식으로 응답해주세요."""
        elif self.language == "en":
            user_prompt = f"""
**Current user input:** "{user_input}"

## Conversation Context
{context_text if context_text.strip() else "(First conversation)"}

## Task Instructions
Please process the user's refund request considering the above conversation context.
Please provide a response in the following JSON format:

{{
    "refund_possible": true/false,
    "refund_fee": number (refund fee, 0 if none),
    "total_refund_amount": number (actual refund amount),
    "reason": "detailed reason for refund possibility/impossibility",
    "user_response": "friendly response to show to user",
    "policy_applied": ["list of applied policies"]
}}

Please respond in accurate JSON format.

IMPORTANT: Your response must be in English only. Do not use Korean or any other language."""
        elif self.language == "jp":
            user_prompt = f"""
**現在のユーザー入力:** "{user_input}"

## 会話コンテキスト
{context_text if context_text.strip() else "(初回会話)"}

## 作業指示
上記の会話コンテキストを考慮してユーザーの返品リクエストを処理してください。
以下の形式のJSONで応答を提供してください:

{{
    "refund_possible": true/false,
    "refund_fee": 数字 (返品手数料、なければ0),
    "total_refund_amount": 数字 (実際の返品金額),
    "reason": "返品可能/不可能な詳細理由",
    "user_response": "ユーザーに表示する親切な応答",
    "policy_applied": ["適用されたポリシーリスト"]
}}

正確なJSON形式で応答してください。

重要: あなたの応答は日本語でのみ行ってください。韓国語や他の言語を使用してはいけません。"""

        # Add language instruction to system prompt for better enforcement
        if self.language == "en":
            system_prompt += "\n\nIMPORTANT: You MUST respond in English only. Never use Korean or other languages."
        elif self.language == "jp":
            system_prompt += "\n\n重要: 必ず日本語でのみ応答してください。韓国語や他の言語は使用しないでください。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages)
        
        # JSON 파싱 시도
        try:
            # JSON 코드 블록 제거
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif "```" in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            parsed_response = json.loads(response.strip())
            
            # 필수 필드 확인 및 기본값 설정
            result = {
                "refund_possible": parsed_response.get("refund_possible", False),
                "refund_fee": parsed_response.get("refund_fee", 0),
                "total_refund_amount": parsed_response.get("total_refund_amount", 0),
                "reason": parsed_response.get("reason", "환불 판단 정보 없음"),
                "user_response": parsed_response.get("user_response", response),
                "policy_applied": parsed_response.get("policy_applied", [])
            }
            
            # 자연스러운 대화체 응답 생성
            result["conversational_response"] = self._generate_conversational_response(result)
            
            return result
            
        except (json.JSONDecodeError, AttributeError) as e:
            # JSON 파싱 실패시 기본 응답 구조 반환
            return {
                "refund_possible": None,
                "refund_fee": 0,
                "total_refund_amount": 0,
                "reason": "JSON 파싱 실패",
                "user_response": response,
                "policy_applied": [],
                "conversational_response": response
            }
    
    def _safe_convert_to_number(self, value) -> float:
        """값을 안전하게 숫자로 변환"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                # 쉼표 제거 후 숫자 변환
                cleaned_value = value.replace(',', '').replace('원', '').strip()
                return float(cleaned_value)
            except (ValueError, AttributeError):
                return 0.0
        else:
            return 0.0
    
    def _generate_conversational_response(self, result: Dict[str, Any]) -> str:
        """Convert structured response to natural conversational style"""
        refund_possible = result.get("refund_possible", False)
        refund_fee = self._safe_convert_to_number(result.get("refund_fee", 0))
        total_amount = self._safe_convert_to_number(result.get("total_refund_amount", 0))
        reason = result.get("reason", "")
        
        if self.language == "ko":
            if refund_possible:
                response = "네, 해당 주문에 대한 환불이 가능합니다! 😊\n\n"
                if refund_fee > 0:
                    response += f"🔸 환불 수수료: {int(refund_fee):,}원\n"
                    response += f"🔸 실제 환불 금액: {int(total_amount):,}원\n\n"
                    response += "환불 시 수수료가 차감되어 처리됩니다. "
                else:
                    response += f"🔸 환불 금액: {int(total_amount):,}원\n\n"
                    response += "수수료 없이 전액 환불해드립니다! "
                response += "환불 처리를 원하시면 말씀해 주세요.\n\n"
                response += f"📝 환불 사유: {reason}"
            else:
                response = "죄송합니다. 해당 주문은 환불이 어려운 상황입니다. 😔\n\n"
                response += f"📝 사유: {reason}\n\n"
                response += "다른 도움이 필요하시면 언제든 말씀해 주세요!"
        
        elif self.language == "en":
            if refund_possible:
                response = "Yes, a refund is possible for this order! 😊\n\n"
                if refund_fee > 0:
                    response += f"🔸 Refund fee: ${int(refund_fee):,}\n"
                    response += f"🔸 Actual refund amount: ${int(total_amount):,}\n\n"
                    response += "The fee will be deducted during refund processing. "
                else:
                    response += f"🔸 Refund amount: ${int(total_amount):,}\n\n"
                    response += "Full refund without any fees! "
                response += "Please let me know if you want to proceed with the refund.\n\n"
                response += f"📝 Refund reason: {reason}"
            else:
                response = "I'm sorry, but this order cannot be refunded. 😔\n\n"
                response += f"📝 Reason: {reason}\n\n"
                response += "If you need any other assistance, please let me know!"
        
        elif self.language == "jp":
            if refund_possible:
                response = "はい、この注文の返品が可能です！😊\n\n"
                if refund_fee > 0:
                    response += f"🔸 返品手数料: {int(refund_fee):,}円\n"
                    response += f"🔸 実際の返品金額: {int(total_amount):,}円\n\n"
                    response += "返品時に手数料が差し引かれて処理されます。"
                else:
                    response += f"🔸 返品金額: {int(total_amount):,}円\n\n"
                    response += "手数料なしで全額返品いたします！"
                response += "返品処理をご希望でしたらお知らせください。\n\n"
                response += f"📝 返品理由: {reason}"
            else:
                response = "申し訳ございませんが、この注文は返品が困難な状況です。😔\n\n"
                response += f"📝 理由: {reason}\n\n"
                response += "他にサポートが必要でしたらいつでもお知らせください！"
        
        return response
    
    @weave.op()
    def handle_with_structured_context(self, user_input: str, structured_context: str) -> Dict[str, Any]:
        """Handle refund inquiry with structured context"""
        
        # Get prompt from Weave (refund policy is already included)
        system_prompt = self.prompt_manager.get_refund_agent_prompt()
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

## 구조화된 대화 맥락
{structured_context if structured_context.strip() else "(첫 대화)"}

## 작업 지시
위 구조화된 대화 맥락을 고려하여 사용자의 환불 요청을 처리해주세요. 
사용자의 입력과 이전 에이전트들의 결과를 적극 활용하여 정확한 환불 판단을 해주세요.

응답은 다음 형식의 JSON으로 제공해주세요:

{{
    "refund_possible": true/false,
    "refund_fee": 숫자 (환불 수수료, 없으면 0),
    "total_refund_amount": 숫자 (실제 환불 금액),
    "reason": "환불 가능/불가능한 상세 이유",
    "user_response": "사용자에게 보여줄 친절한 응답",
    "policy_applied": ["적용된 정책 목록"]
}}

정확한 JSON 형식으로 응답해주세요."""
        elif self.language == "en":
            user_prompt = f"""
**Current user input:** "{user_input}"

## Structured Conversation Context
{structured_context if structured_context.strip() else "(First conversation)"}

## Task Instructions
Please process the user's refund request considering the above structured conversation context.
Actively utilize the user's input and results from previous agents to make accurate refund judgments.

Please provide a response in the following JSON format:

{{
    "refund_possible": true/false,
    "refund_fee": number (refund fee, 0 if none),
    "total_refund_amount": number (actual refund amount),
    "reason": "detailed reason for refund possibility/impossibility",
    "user_response": "friendly response to show to user",
    "policy_applied": ["list of applied policies"]
}}

Please respond in accurate JSON format.

IMPORTANT: Your response must be in English only. Do not use Korean or any other language."""
        elif self.language == "jp":
            user_prompt = f"""
**現在のユーザー入力:** "{user_input}"

## 構造化された会話コンテキスト
{structured_context if structured_context.strip() else "(初回会話)"}

## 作業指示
上記の構造化された会話コンテキストを考慮してユーザーの返品リクエストを処理してください。
ユーザーの入力と以前のエージェントの結果を積極的に活用して正確な返品判断をしてください。

以下の形式のJSONで応答を提供してください:

{{
    "refund_possible": true/false,
    "refund_fee": 数字 (返品手数料、なければ0),
    "total_refund_amount": 数字 (実際の返品金額),
    "reason": "返品可能/不可能な詳細理由",
    "user_response": "ユーザーに表示する親切な応答",
    "policy_applied": ["適用されたポリシーリスト"]
}}

正確なJSON形式で応答してください。

重要: あなたの応答は日本語でのみ行ってください。韓国語や他の言語を使用してはいけません。"""

        # Add language instruction to system prompt for better enforcement
        if self.language == "en":
            system_prompt += "\n\nIMPORTANT: You MUST respond in English only. Never use Korean or other languages."
        elif self.language == "jp":
            system_prompt += "\n\n重要: 必ず日本語でのみ応答してください。韓国語や他の言語は使用しないでください。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages)
        
        # JSON 파싱 시도
        try:
            # JSON 코드 블록 제거
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif "```" in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            parsed_response = json.loads(response.strip())
            
            # 필수 필드 확인 및 기본값 설정
            result = {
                "refund_possible": parsed_response.get("refund_possible", False),
                "refund_fee": parsed_response.get("refund_fee", 0),
                "total_refund_amount": parsed_response.get("total_refund_amount", 0),
                "reason": parsed_response.get("reason", "환불 판단 정보 없음"),
                "user_response": parsed_response.get("user_response", response),
                "policy_applied": parsed_response.get("policy_applied", [])
            }
            
            # 자연스러운 대화체 응답 생성
            result["conversational_response"] = self._generate_conversational_response(result)
            
            return result
            
        except (json.JSONDecodeError, AttributeError) as e:
            # JSON 파싱 실패시 기본 응답 구조 반환
            return {
                "refund_possible": None,
                "refund_fee": 0,
                "total_refund_amount": 0,
                "reason": "JSON 파싱 실패",
                "user_response": response,
                "policy_applied": [],
                "conversational_response": response
            }