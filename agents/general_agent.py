"""
General Response Agent
"""
import weave
from typing import List, Dict, Any
from .base import LLMClient
from prompts.weave_prompts import prompt_manager


class GeneralAgent:
    """General Response Agent"""
    
    def __init__(self, llm_client: LLMClient, language: str = None):
        self.llm = llm_client
        from config import config
        from prompts.weave_prompts import WeavePromptManager
        self.language = language or config.LANGUAGE
        # Create dedicated prompt manager for this agent
        self.prompt_manager = WeavePromptManager()
        self.prompt_manager.set_language(self.language)
    
    @weave.op()
    def handle(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """일반 문의 처리"""
        
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
        
        # Get prompt from Weave
        system_prompt = self.prompt_manager.get_general_agent_prompt()
        
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
Please respond considering the above conversation context.

IMPORTANT: Your response must be in English only. Do not use Korean or any other language."""
        elif self.language == "jp":
            user_prompt = f"""
## 現在のユーザー入力: {user_input}

## 会話コンテキスト
{context_text if context_text.strip() else "(初回会話)"}

## 作業指示
上記の会話コンテキストを考慮して応答してください。

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
        
        return self.llm.chat(messages)
    
    @weave.op()
    def handle_with_structured_context(self, user_input: str, structured_context: str) -> str:
        """Handle general inquiry with structured context"""
        
        # Get prompt from Weave
        system_prompt = self.prompt_manager.get_general_agent_prompt()
        
        # Create localized user prompt
        if self.language == "ko":
            user_prompt = f"""
## 현재 사용자 입력: {user_input}

## 구조화된 대화 맥락
{structured_context if structured_context.strip() else "(첫 대화)"}

## 작업 지시
위 구조화된 대화 맥락을 고려하여 친근하고 도움이 되는 응답을 해주세요.
특히 이전 에이전트들의 결과를 종합하여 최종적으로 사용자에게 도움이 되는 응답을 제공해주세요."""
        elif self.language == "en":
            user_prompt = f"""
## Current user input: {user_input}

## Structured conversation context
{structured_context if structured_context.strip() else "(First conversation)"}

## Task Instructions
Please provide a friendly and helpful response considering the above structured conversation context.
Especially, synthesize the results from previous agents to provide a final response that is helpful to the user.

IMPORTANT: Your response must be in English only. Do not use Korean or any other language."""
        elif self.language == "jp":
            user_prompt = f"""
## 現在のユーザー入力: {user_input}

## 構造化された会話コンテキスト
{structured_context if structured_context.strip() else "(初回会話)"}

## 作業指示
上記の構造化された会話コンテキストを考慮して親しみやすく役立つ応答をしてください。
特に、以前のエージェントの結果を総合して、最終的にユーザーに役立つ応答を提供してください。

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
        
        return self.llm.chat(messages)