"""
Intent Classification Agent
"""
import weave
import json
from typing import List, Dict, Any
from datetime import datetime
from .base import LLMClient
from prompts.weave_prompts import prompt_manager
from config import config


class IntentAgent:
    """Intent analysis agent"""
    
    def __init__(self, llm_client: LLMClient, language: str = None):
        self.llm = llm_client
        from prompts.weave_prompts import WeavePromptManager
        self.language = language or config.LANGUAGE
        # Create dedicated prompt manager for this agent
        self.prompt_manager = WeavePromptManager()
        self.prompt_manager.set_language(self.language)
    
    @weave.op()
    def classify(self, user_input: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify user input intent"""
        
        # Prepare conversation history
        history_text = ""
        if context:
            recent_turns = context[-3:]  # Only recent 3 turns
            for turn in recent_turns:
                if self.language == "ko":
                    history_text += f"사용자: {turn.get('user', '')}\n봇: {turn.get('bot', '')}\n"
                elif self.language == "en":
                    history_text += f"User: {turn.get('user', '')}\nBot: {turn.get('bot', '')}\n"
                elif self.language == "jp":
                    history_text += f"ユーザー: {turn.get('user', '')}\nボット: {turn.get('bot', '')}\n"
        
        # Get prompt from Weave
        system_prompt = self.prompt_manager.get_intent_prompt(
            current_date=config.CURRENT_DATE
        )
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
**현재 사용자 입력:** "{user_input}"

**대화 히스토리:**
{history_text if history_text.strip() else "(첫 대화)"}

## 작업
위 사용자 입력을 분석하여 의도를 분류하고 엔티티를 추출하세요.

**출력 형식 (JSON만):**
{{
    "intent": "분류된_의도",
    "confidence": 0.95,
    "entities": {{
        "order_id": "ORD번호_또는_null",
        "product_name": "상품명_또는_null", 
        "time_reference": "시간표현_또는_null",
        "quantity": 숫자_또는_null,
        "refund_reason": "사유_또는_null",
        "refund_reference": true_또는_false,
        "selection_type": "선택유형_또는_null"
    }}
}}"""
        elif self.language == "en":
            user_prompt = f"""
**Current user input:** "{user_input}"

**Conversation history:**
{history_text if history_text.strip() else "(First conversation)"}

## Task
Analyze the above user input to classify intent and extract entities.

**Output format (JSON only):**
{{
    "intent": "classified_intent",
    "confidence": 0.95,
    "entities": {{
        "order_id": "ORD_number_or_null",
        "product_name": "product_name_or_null", 
        "time_reference": "time_expression_or_null",
        "quantity": number_or_null,
        "refund_reason": "reason_or_null",
        "refund_reference": true_or_false,
        "selection_type": "selection_type_or_null"
    }}
}}"""
        elif self.language == "jp":
            user_prompt = f"""
**現在のユーザー入力:** "{user_input}"

**会話履歴:**
{history_text if history_text.strip() else "(初回会話)"}

## タスク
上記のユーザー入力を分析して意図を分類し、エンティティを抽出してください。

**出力形式 (JSONのみ):**
{{
    "intent": "分類された意図",
    "confidence": 0.95,
    "entities": {{
        "order_id": "ORD番号_またはnull",
        "product_name": "商品名_またはnull", 
        "time_reference": "時間表現_またはnull",
        "quantity": 数字_またはnull,
        "refund_reason": "理由_またはnull",
        "refund_reference": true_またはfalse,
        "selection_type": "選択タイプ_またはnull"
    }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.3)
        
        try:
            # JSON 마크다운 블록 제거
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"[DEBUG] JSON parsing failed: {e}")
            print(f"[DEBUG] Original response: {repr(response)}")
            # Default values when JSON parsing fails
            return {
                "intent": "general_chat",
                "confidence": 0.5,
                "entities": {}
            }
