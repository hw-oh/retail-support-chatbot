#!/usr/bin/env python3
"""
Weave 프롬프트 등록 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weave
from prompts.weave_prompts import register_all_prompts, WeavePromptManager


def main():
    """프롬프트 등록 메인 함수"""
    print("🚀 Weave 프롬프트 등록 시작")
    
    # Weave 초기화
    weave.init("retail-chatbot-dev")
    print("✅ Weave 초기화 완료")
    
    # 모든 프롬프트 등록
    prompt_refs = register_all_prompts()
    
    # 등록된 프롬프트 테스트
    print("\n🔍 등록된 프롬프트 테스트:")
    manager = WeavePromptManager()
    
    try:
        intent_prompt = manager.get_intent_prompt()
        print(f"✅ Intent 프롬프트: {len(intent_prompt)} 문자")
        
        order_prompt = manager.get_order_agent_prompt()
        print(f"✅ Order 프롬프트: {len(order_prompt)} 문자")
        
        refund_prompt = manager.get_refund_agent_prompt()
        print(f"✅ Refund 프롬프트: {len(refund_prompt)} 문자")
        
        general_prompt = manager.get_general_agent_prompt()
        print(f"✅ General 프롬프트: {len(general_prompt)} 문자")
        
    except Exception as e:
        print(f"⚠️ 프롬프트 테스트 실패: {e}")
    
    print("\n🎉 프롬프트 등록 및 테스트 완료!")
    print("\n📖 등록된 프롬프트:")
    for key, value in prompt_refs.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
