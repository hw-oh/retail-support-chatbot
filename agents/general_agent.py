"""
General Response Agent
"""
import weave
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class GeneralAgent:
    """일반 응답 에이전트"""
    
    def __init__(self, llm_client: LLMClient, language: str = None):
        self.llm = llm_client
        from config import config
        self.language = language or config.LANGUAGE
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """일반 문의 처리"""
        
        # 대화 컨텍스트 준비
        context_text = ""
        if context:
            recent_turns = context[-3:]  # 최근 3턴
            for turn in recent_turns:
                context_text += f"사용자: {turn.get('user', '')}\n"
                context_text += f"봇: {turn.get('bot', '')}\n\n"
        
        # Get prompt from Weave
        prompt_manager.set_language(self.language)
        system_prompt = prompt_manager.get_general_agent_prompt()
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
## 현재 사용자 입력: {user_input}

## 대화 맥락
{context_text if context_text.strip() else "(첫 대화)"}

## 작업 지시
위 대화 맥락을 고려하여 응답해주세요."""
        elif self.language == "en":
            user_prompt = f"""
## Current user input: {user_input}

## Conversation Context
{context_text if context_text.strip() else "(First conversation)"}

## Task Instructions
Please respond considering the above conversation context."""
        elif self.language == "jp":
            user_prompt = f"""
## 現在のユーザー入力: {user_input}

## 会話コンテキスト
{context_text if context_text.strip() else "(初回会話)"}

## 作業指示
上記の会話コンテキストを考慮して応答してください。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)
    
    @weave.op()
    def handle_with_structured_context(self, user_input: str, structured_context: str) -> str:
        """구조화된 컨텍스트를 사용한 일반 문의 처리"""
        
        # Weave에서 프롬프트 가져오기
        system_prompt = prompt_manager.get_general_agent_prompt()
        user_prompt = f"""
## 현재 사용자 입력: {user_input}

## 구조화된 대화 맥락
{structured_context if structured_context.strip() else "(첫 대화)"}

## 작업 지시
위 구조화된 대화 맥락을 고려하여 친근하고 도움이 되는 응답을 해주세요.
특히 이전 에이전트들의 결과를 종합하여 최종적으로 사용자에게 도움이 되는 응답을 제공해주세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.llm.chat(messages)