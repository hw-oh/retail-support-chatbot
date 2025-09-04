#!/usr/bin/env python3
"""
Weave 프롬프트 등록 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weave
from prompts.weave_prompts import register_all_prompts, WeavePromptManager
from config import config


def _determine_languages_from_args() -> list:
    """CLI 인자에서 등록 대상 언어 목록을 결정합니다."""
    if len(sys.argv) > 1:
        lang_arg = sys.argv[1].lower()
        if lang_arg == "all":
            return list(config.SUPPORTED_LANGUAGES)
        if lang_arg in config.SUPPORTED_LANGUAGES:
            return [lang_arg]
        print(f"❌ 지원하지 않는 언어: {lang_arg}")
        print(f"지원 언어: {', '.join(config.SUPPORTED_LANGUAGES)} 또는 'all'")
        sys.exit(1)
    # 무인자 실행: 모든 언어 일괄 등록
    return list(config.SUPPORTED_LANGUAGES)


def _test_registered_prompts(language: str):
    """등록된 프롬프트를 간단히 호출해 길이를 출력합니다."""
    manager = WeavePromptManager()
    manager.set_language(language)
    try:
        intent_prompt = manager.get_intent_prompt()
        order_prompt = manager.get_order_agent_prompt()
        refund_prompt = manager.get_refund_agent_prompt()
        general_prompt = manager.get_general_agent_prompt()
        print(f"   - Intent: {len(intent_prompt)} chars | Order: {len(order_prompt)} | Refund: {len(refund_prompt)} | General: {len(general_prompt)}")
    except Exception as e:
        print(f"   ⚠️ 테스트 실패: {e}")


def main():
    """프롬프트 등록 메인 함수 (언어별/전체 등록 지원)"""
    print("🚀 Weave 프롬프트 등록 시작")

    # Weave 초기화
    weave.init("retail-chatbot-dev")
    print("✅ Weave 초기화 완료")

    # 대상 언어 결정
    target_languages = _determine_languages_from_args()
    print(f"🌍 등록 대상 언어: {', '.join([lang.upper() for lang in target_languages])}")

    all_refs = {}
    for lang in target_languages:
        print(f"\n🔄 {lang.upper()} 프롬프트 등록 중...")
        refs = register_all_prompts(language=lang)
        all_refs[lang] = refs
        print(f"✅ {lang.upper()} 프롬프트 등록 완료")
        print("   🔍 간단 테스트:")
        _test_registered_prompts(lang)

    print("\n🎉 프롬프트 등록(언어별) 완료!")
    print("\n📖 등록된 프롬프트 요약:")
    for lang, refs in all_refs.items():
        print(f"- {lang.upper()}")
        for key, value in refs.items():
            print(f"    · {key}: {value}")


if __name__ == "__main__":
    main()
