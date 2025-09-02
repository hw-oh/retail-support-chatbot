import json
import weave
import asyncio
from typing import Dict, List, Any
from simple_chatbot import SimplifiedChatbot
from scorers.policy_compliance_scorer import PolicyComplianceScorer
from scorers.reason_quality_scorer import ReasonQualityScorer
from scorers.refund_decision_scorer import RefundDecisionScorer
from config import config

class RefundChatbotModel(weave.Model):
    """환불 챗봇 평가를 위한 Weave Model 클래스"""
    
    @weave.op()
    def predict(self, user_query: str, order_info: Dict = None) -> Dict[str, Any]:
        """
        사용자 쿼리에 대한 챗봇 응답을 예측
        
        Args:
            user_query: 사용자 질문
            order_info: 주문 정보 (선택적)
        
        Returns:
            챗봇 응답과 분석 결과
        """
        try:
            # 챗봇 인스턴스 생성 및 응답 생성
            chatbot = SimplifiedChatbot()
            response = chatbot.chat(user_query)
            
            return {
                "response": response,
                "raw_response": response
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "raw_response": f"Error: {str(e)}"
            }

# 평가 함수들 정의
@weave.op()
def policy_compliance_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """정책 준수도 평가 - LLM 기반으로 점수와 이유 반환"""
    scorer = PolicyComplianceScorer()
    result = scorer.score(target, output)
    return {
        "accuracy": result.get("policy_compliance", 0.0),
        "reason": result.get("reason", "평가 실패")
    }

@weave.op()
def reasoning_performance_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """추론 성능 평가 - LLM 기반으로 점수와 이유 반환"""
    scorer = ReasonQualityScorer()
    result = scorer.score(target, output)
    return {
        "accuracy": result.get("reason_score", 0.0),
        "reason": result.get("reason", "평가 실패")
    }

@weave.op()
def refund_accuracy_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """환불 정확도 평가 - LLM 기반 평가 (전체/환불/수수료 정확도 + 이유)"""
    scorer = RefundDecisionScorer()
    result = scorer.score(target, output)
    return {
        "accuracy": result.get("accuracy", 0.0),  # 전체 정확도
        "accuracy_refund": result.get("accuracy_refund", 0.0),  # 환불 가능 여부 정확도
        "accuracy_fee": result.get("accuracy_fee", 0.0),  # 환불 수수료 정확도
        "reason": result.get("reason", "평가 결과 없음")
    }

def load_evaluation_dataset():
    """평가 데이터셋 로드 및 current_date 추출"""
    with open('data/evaluate_refund.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 데이터셋의 current_date 추출 (있다면)
    dataset_current_date = data.get("dataset_info", {}).get("current_date")
    if not dataset_current_date:
        # current_date가 없다면 created_date를 사용
        dataset_current_date = data.get("dataset_info", {}).get("created_date", config.CURRENT_DATE)
    
    # 새로운 JSON 구조에서 test_cases 배열 추출
    test_cases = data.get("test_cases", [])
    
    # Weave Evaluation 형식으로 변환
    examples = []
    for item in test_cases:
        example = {
            "id": item["test_id"],
            "user_query": item["user_query"],
            "order_info": item["order_info"],
            "scenario": item["scenario"],
            "target": item["expected_result"]
        }
        examples.append(example)
    
    return examples, dataset_current_date

async def main():
    # Weave 초기화
    weave.init('retail-chatbot-dev')
    
    # 모델 생성
    model = RefundChatbotModel()
    
    # 데이터셋 로드 및 현재 날짜 설정
    examples, dataset_current_date = load_evaluation_dataset()
    print(f"📊 {len(examples)}개의 테스트 시나리오 로드됨")
    
    # 평가용 날짜 설정 (원래 날짜 백업)
    original_date = config.CURRENT_DATE
    config.CURRENT_DATE = dataset_current_date
    print(f"📅 평가용 날짜 설정: {dataset_current_date} (원래: {original_date})")
    
    # 평가 설정 - 3가지 핵심 평가만 수행
    evaluation = weave.Evaluation(
        name="refund_chatbot_simplified_evaluation",
        dataset=examples,
        scorers=[
            policy_compliance_evaluation,      # 정책 준수
            reasoning_performance_evaluation,  # 추론 성능
            refund_accuracy_evaluation        # 환불 정확도
        ]
    )
    
    print("🚀 환불 챗봇 평가 시작...")
    print("📋 평가 항목:")
    print("   1. 정책 준수 (Policy Compliance) - LLM 기반 평가 (점수 + 이유)")
    print("   2. 추론 성능 (Reasoning Performance) - LLM 기반 평가 (점수 + 이유)")
    print("   3. 환불 정확도 (Refund Accuracy) - LLM 기반 평가 (전체/환불/수수료 정확도 + 이유)")
    
    try:
        # 평가 실행
        results = await evaluation.evaluate(model)
        
        print("\n✅ 평가 완료!")
        print(f"📈 결과: {results}")
        
        return results
    
    finally:
        # 평가 완료 후 원래 날짜로 복원
        config.CURRENT_DATE = original_date
        print(f"🔄 날짜 복원: {original_date}")

if __name__ == "__main__":
    asyncio.run(main())