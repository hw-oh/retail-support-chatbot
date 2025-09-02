#!/usr/bin/env python3
"""
Weave 프롬프트 등록 및 관리
"""
import weave
from datetime import datetime
from .intent_prompts import INTENT_PROMPTS
from .agent_prompts import AGENT_PROMPTS
from config import config


# 환불 정책 로드
def load_refund_policy():
    try:
        import os
        policy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'refund_policy.txt')
        with open(policy_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "환불 정책 파일을 찾을 수 없습니다."

def register_all_prompts():
    """모든 프롬프트를 Weave에 등록 (공식 StringPrompt 클래스 사용)"""
    
    print("🔄 Weave에 프롬프트 등록 중...")
    
    # Weave StringPrompt 클래스를 사용한 프롬프트 등록
    prompts_to_register = {
        "intent_classifier_korean": {
            "content": INTENT_PROMPTS["ko"]["system"],
            "description": "한국어 쇼핑몰 고객 서비스 의도 분류 프롬프트 (템플릿 변수: {current_date})"
        },
        "order_agent_system": {
            "content": AGENT_PROMPTS["order_agent"]["system"],
            "description": "주문 조회 및 관리 전문 에이전트 시스템 프롬프트"
        },
        "refund_agent_system": {
            "content": AGENT_PROMPTS["refund_agent"]["system"] % load_refund_policy(),
            "description": "환불 처리 및 정책 안내 전문 에이전트 시스템 프롬프트"
        },
        "general_agent_system": {
            "content": AGENT_PROMPTS["general_agent"]["system"],
            "description": "일반 고객 서비스 응답 에이전트 시스템 프롬프트"
        }
    }
    
    registered_refs = {}
    
    for name, prompt_info in prompts_to_register.items():
        try:
            # 공식 StringPrompt 클래스 사용
            prompt_obj = weave.StringPrompt(prompt_info["content"])
            weave.publish(prompt_obj, name=name)
            registered_refs[name] = name
            print(f"✅ {name} 프롬프트 등록 완료 - {prompt_info['description']}")
        except Exception as e:
            print(f"⚠️ {name} 프롬프트 등록 실패: {e}")
            # 로컬 프롬프트로 폴백
            registered_refs[name] = name
    
    print("🎉 모든 프롬프트 등록 완료!")
    return {
        "intent_classifier": "intent_classifier_korean",
        "order_agent": "order_agent_system", 
        "refund_agent": "refund_agent_system",
        "general_agent": "general_agent_system"
    }


def get_prompt_from_weave(prompt_name: str, **kwargs) -> str:
    """Weave에서 StringPrompt 객체를 가져와서 format() 호출 (Weave 없이도 동작)"""
    
    # Weave가 비활성화되어 있으면 바로 로컬 프롬프트 사용
    import os
    if os.getenv('WEAVE_INIT_DISABLED') == '1':
        return get_fallback_prompt(prompt_name, **kwargs)
    
    try:
        # Weave에서 StringPrompt 객체 가져오기
        ref = weave.ref(prompt_name)
        prompt_obj = ref.get()
        
        # StringPrompt.format() 메서드 사용
        if kwargs:
            return prompt_obj.format(**kwargs)
        else:
            return prompt_obj.format()
        
    except Exception as e:
        # 개발/테스트 환경에서는 조용히 폴백
        if os.getenv('WEAVE_INIT_DISABLED') == '1':
            pass  # 조용히 폴백
        else:
            print(f"⚠️ Weave에서 프롬프트를 가져오는데 실패 ({prompt_name}): {e}")
            print("📁 로컬 프롬프트로 폴백합니다.")
        
        # 폴백: 로컬 프롬프트 사용
        return get_fallback_prompt(prompt_name, **kwargs)


def get_fallback_prompt(prompt_name: str, **kwargs) -> str:
    """Weave 실패시 로컬 프롬프트 폴백"""
    
    fallback_prompts = {
        "intent_classifier_korean": INTENT_PROMPTS["ko"]["system"],
        "order_agent_system": AGENT_PROMPTS["order_agent"]["system"],
        "refund_agent_system": AGENT_PROMPTS["refund_agent"]["system"] % load_refund_policy(),
        "general_agent_system": AGENT_PROMPTS["general_agent"]["system"]
    }
    
    prompt = fallback_prompts.get(prompt_name, "프롬프트를 찾을 수 없습니다.")
    
    if kwargs:
        return prompt.format(**kwargs)
    return prompt


class WeavePromptManager:
    """프롬프트 관리자 - 개발 모드에서는 로컬 프롬프트 직접 사용"""
    
    def __init__(self, use_local_only: bool = None):
        """
        Args:
            use_local_only: True면 항상 로컬 프롬프트 사용, None이면 환경변수로 결정
        """
        import os
        if use_local_only is None:
            # 환경변수로 결정 (기본값: 로컬 사용)
            self.use_local_only = os.getenv('USE_LOCAL_PROMPTS', '1') == '1'
        else:
            self.use_local_only = use_local_only
            
        self.prompt_refs = {
            "intent_classifier": "intent_classifier_korean",
            "order_agent": "order_agent_system",
            "refund_agent": "refund_agent_system", 
            "general_agent": "general_agent_system"
        }
    
    def get_intent_prompt(self, current_date: str = None) -> str:
        """의도 분류 프롬프트 가져오기"""
        if current_date is None:
            current_date = config.CURRENT_DATE
        
        if self.use_local_only:
            # 로컬 프롬프트 직접 사용 (즉시 반영)
            prompt = INTENT_PROMPTS["ko"]["system"]
            return prompt.format(current_date=current_date)
        else:
            # Weave 프롬프트 사용
            return get_prompt_from_weave(
                self.prompt_refs["intent_classifier"],
                current_date=current_date
            )
    
    def get_order_agent_prompt(self) -> str:
        """주문 에이전트 프롬프트 가져오기"""
        if self.use_local_only:
            return AGENT_PROMPTS["order_agent"]["system"]
        else:
            return get_prompt_from_weave(self.prompt_refs["order_agent"])
    
    def get_refund_agent_prompt(self) -> str:
        """환불 에이전트 프롬프트 가져오기"""
        if self.use_local_only:
            return AGENT_PROMPTS["refund_agent"]["system"] % load_refund_policy()
        else:
            return get_prompt_from_weave(self.prompt_refs["refund_agent"])
    
    def get_general_agent_prompt(self) -> str:
        """일반 에이전트 프롬프트 가져오기"""
        if self.use_local_only:
            return AGENT_PROMPTS["general_agent"]["system"]
        else:
            return get_prompt_from_weave(self.prompt_refs["general_agent"])


# 전역 프롬프트 매니저 인스턴스
prompt_manager = WeavePromptManager()


if __name__ == "__main__":
    # Weave 초기화
    weave.init("retail-chatbot-dev")
    
    # 프롬프트 등록
    register_all_prompts()
    
    # 테스트
    print("\n🔍 프롬프트 테스트:")
    manager = WeavePromptManager()
    intent_prompt = manager.get_intent_prompt()
    print(f"Intent 프롬프트 길이: {len(intent_prompt)} 문자")
    
    order_prompt = manager.get_order_agent_prompt()
    print(f"Order 프롬프트 길이: {len(order_prompt)} 문자")
