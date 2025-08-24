#!/usr/bin/env python3
"""
쇼핑몰 챗봇 메인 실행 파일
"""
import os
import sys
from datetime import datetime
from agents import ShoppingMallAgent
from config import config


def print_welcome():
    """환영 메시지 출력"""
    print("\n" + "="*60)
    print("🛍️  쇼핑몰 고객 서비스 챗봇에 오신 것을 환영합니다!")
    print("="*60)
    print("\n💬 제품 검색, 주문 조회, 환불 문의 등을 도와드릴 수 있습니다.")
    print("📝 대화를 종료하려면 'exit', 'quit', '종료' 중 하나를 입력하세요.")
    print("🔄 새로운 대화를 시작하려면 'new', '새로고침'을 입력하세요.\n")
    

def print_divider():
    """구분선 출력"""
    print("-" * 60)


def is_exit_command(text: str) -> bool:
    """종료 명령어 확인"""
    exit_commands = ['exit', 'quit', '종료', '끝', '나가기']
    return text.lower().strip() in exit_commands


def is_new_session_command(text: str) -> bool:
    """새 세션 시작 명령어 확인"""
    new_commands = ['new', 'reset', '새로고침', '새대화', '새로운 대화']
    return text.lower().strip() in new_commands


def format_response(response: dict):
    """응답 포맷팅 및 출력"""
    print("\n🤖 챗봇:")
    print(response.get("response", ""))
    
    # 디버그 정보 (옵션)
    if os.getenv("DEBUG", "").lower() == "true":
        print(f"\n[DEBUG] 의도: {response.get('intent')} (신뢰도: {response.get('confidence', 0):.2f})")
        if response.get("entities"):
            print(f"[DEBUG] 추출된 정보: {response.get('entities')}")


def main():
    """메인 실행 함수"""
    # API 키 확인
    if not config.OPENAI_API_KEY:
        print("❌ 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY를 설정하거나 환경 변수로 설정해주세요.")
        sys.exit(1)
    
    print_welcome()
    
    # 에이전트 초기화
    try:
        agent = ShoppingMallAgent()
        print("✅ 챗봇이 준비되었습니다. 무엇을 도와드릴까요?")
    except Exception as e:
        print(f"❌ 챗봇 초기화 실패: {e}")
        sys.exit(1)
    
    # 세션 ID
    session_id = None
    
    # 대화 루프
    with weave.thread() as thread_ctx:
        print(f"Thread ID: {thread_ctx.thread_id}")
        while True:
            try:
                print_divider()
                
                # 사용자 입력
                user_input = input("\n👤 고객님: ").strip()
                
                # 빈 입력 처리
                if not user_input:
                    print("💡 메시지를 입력해주세요.")
                    continue
                
                # 종료 명령어 확인
                if is_exit_command(user_input):
                    print("\n👋 이용해주셔서 감사합니다. 좋은 하루 되세요!")
                    break
                
                # 새 세션 시작
                if is_new_session_command(user_input):
                    session_id = None
                    print("\n🔄 새로운 대화를 시작합니다.")
                    print_welcome()
                    continue
                
                # 처리 중 메시지
                print("\n⏳ 답변을 준비하고 있습니다...")
                
                # 메시지 처리
                response = agent.process_message(user_input, session_id)
                session_id = response.get("session_id")
                
                # 응답 출력
                format_response(response)
                
                # 확인이 필요한 경우 안내
                if response.get("needs_confirmation"):
                    print("\n💡 위 내용을 확인하시고 진행 여부를 말씀해주세요. (네/아니요)")
                
            except KeyboardInterrupt:
                print("\n\n👋 대화가 중단되었습니다. 이용해주셔서 감사합니다!")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                print("💡 다시 시도해주세요.")
    
    # 세션 정리
    if session_id:
        agent.clear_session(session_id)
    
    print("\n" + "="*60)
    print("챗봇을 종료합니다. 감사합니다! 🙏")
    print("="*60 + "\n")


if __name__ == "__main__":
    import weave
    weave.init("wandb-korea/retail-chatbot-dev")
    main()
