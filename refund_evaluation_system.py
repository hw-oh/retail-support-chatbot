import json
import weave
import asyncio
from typing import Dict, List, Any
from simple_chatbot import SimplifiedChatbot
# 스코어링 함수들은 get_scoring_functions()에서 동적으로 import

class RefundChatbotModel(weave.Model):
    """환불 챗봇 평가를 위한 Weave Model 클래스 (단일 챗 사용)"""
    
    @weave.op()
    def predict(self, user_query: str) -> Dict[str, Any]:
        """
        사용자 쿼리에 대한 챗봇 응답을 예측 (단일 챗 방식)
        
        Args:
            user_query: 사용자 질문
        
        Returns:
            챗봇 응답
        """
        try:
            # 새로운 챗봇 인스턴스로 단일 대화
            chatbot = SimplifiedChatbot()
            response = chatbot.chat(user_query)
            
            # 챗봇의 conversation_context에서 agent_data 추출
            agent_data = None
            if chatbot.conversation_context:
                last_turn = chatbot.conversation_context[-1]
                agent_data = last_turn.get('agent_data')
            
            result = {
                "response": response,
                "user_query": user_query
            }
            
            # agent_data가 있으면 포함
            if agent_data:
                result["agent_data"] = agent_data
            
            return result
            
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "user_query": user_query,
                "error": str(e)
            }

def load_evaluation_dataset() -> List[Dict]:
    """평가 데이터셋 로드 및 Weave 형식으로 변환"""
    with open('data/evaluate_refund.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    examples = []
    for item in data:
        example = {
            "id": item["test_id"],
            "user_query": item["user_query"],
            "scenario": item["scenario"],
            "order_info": item["order_info"],
            "expected_result": item["expected_result"]
        }
        examples.append(example)
    
    return examples

def get_scoring_functions():
    """스코어링 함수들을 반환 (Weave에 자동 등록됨)"""
    print("📝 스코어링 함수들 준비 중...")
    
    # 새로운 간단한 스코어링 함수들 (이미 @weave.op()로 등록됨)
    from scorers import (
        exact_match_refund_decision,
        llm_judge_reason_quality,
        exact_match_refund_fee,
        llm_judge_policy_compliance
    )
    
    scorers = [
        exact_match_refund_decision,
        llm_judge_reason_quality,
        exact_match_refund_fee,
        llm_judge_policy_compliance
    ]
    
    print("✅ 모든 스코어링 함수 준비 완료")
    return scorers

async def run_comprehensive_evaluation():
    """전체 평가 시스템 실행"""
    # Weave 초기화
    weave.init('retail-chatbot-dev')
    
    # 스코어링 함수들 가져오기
    scorers = get_scoring_functions()
    
    # 모델 생성
    model = RefundChatbotModel()
    
    # 데이터셋 로드
    examples = load_evaluation_dataset()
    print(f"📊 {len(examples)}개의 테스트 시나리오 로드됨")
    
    # 평가 설정
    evaluation = weave.Evaluation(
        name="comprehensive_refund_evaluation",
        dataset=examples,
        scorers=scorers
    )
    
    print("🚀 종합 환불 챗봇 평가 시작...")
    
    # 평가 실행
    results = await evaluation.evaluate(model)
    
    print("✅ 평가 완료!")
    print(f"📈 결과 요약:")
    
    # 결과 분석
    if hasattr(results, 'summary'):
        for scorer_name, score in results.summary.items():
            print(f"  - {scorer_name}: {score:.3f}")
    
    return results

async def run_sample_evaluation(sample_size: int = 5):
    """샘플 평가 실행 (개발/테스트용)"""
    # Weave 초기화
    weave.init('retail-chatbot-dev')
    
    # 스코어링 함수들 가져오기
    scorer_functions = get_scoring_functions()
    
    # 모델 생성
    model = RefundChatbotModel()
    
    # 샘플 데이터
    all_examples = load_evaluation_dataset()
    examples = all_examples[:sample_size]
    
    print(f"📊 {len(examples)}개의 샘플 시나리오로 테스트...")
    
    results = []
    
    for i, example in enumerate(examples, 1):
        print(f"\n🧪 [{i}/{len(examples)}] {example['id']} - {example['scenario']}")
        print(f"👤 질문: {example['user_query']}")
        
        # 모델 예측
        prediction = model.predict(example['user_query'])
        print(f"🤖 응답: {prediction['response'][:100]}...")
        
        # 각 스코어러로 평가
        scores = {}
        scorer_names = ['exact_match_refund_decision', 'llm_judge_reason_quality', 'exact_match_refund_fee', 'llm_judge_policy_compliance']
        
        for i, scorer_func in enumerate(scorer_functions):
            scorer_name = scorer_names[i]
            try:
                score_result = scorer_func(example['expected_result'], prediction)
                scores[scorer_name] = score_result
                # print(f"DEBUG {scorer_name} 결과: {score_result}")
            except Exception as e:
                print(f"⚠️ {scorer_name} 평가 실패: {e}")
                scores[scorer_name] = {"error": str(e)}
        
        # 결과 출력
        print(f"📊 평가 결과:")
        for scorer_name, score_data in scores.items():
            if isinstance(score_data, dict) and "error" not in score_data:
                main_score = None
                # 새로운 스코어링 함수의 키에 맞춰 조정
                if "refund_decision_accuracy" in score_data:
                    main_score = score_data["refund_decision_accuracy"]
                elif "reason_quality_score" in score_data:
                    main_score = score_data["reason_quality_score"]
                elif "refund_fee_accuracy" in score_data:
                    main_score = score_data["refund_fee_accuracy"]
                elif "policy_compliance_score" in score_data:
                    main_score = score_data["policy_compliance_score"]
                
                if main_score is not None:
                    print(f"  - {scorer_name}: {main_score:.3f}")
                else:
                    print(f"  - {scorer_name}: {score_data}")
            elif isinstance(score_data, dict) and "error" in score_data:
                print(f"  - {scorer_name}: ERROR ({score_data['error']})")
            else:
                print(f"  - {scorer_name}: {score_data}")
        
        results.append({
            "example": example,
            "prediction": prediction,
            "scores": scores
        })
    
    # 전체 요약
    print(f"\n📈 샘플 평가 완료! ({len(results)}개 시나리오)")
    
    # 평균 점수 계산
    scorer_averages = {}
    scorer_names = ['exact_match_refund_decision', 'llm_judge_reason_quality', 'exact_match_refund_fee', 'llm_judge_policy_compliance']
    for scorer_name in scorer_names:
        valid_scores = []
        for result in results:
            score_data = result["scores"].get(scorer_name, {})
            if isinstance(score_data, dict) and "error" not in score_data:
                if "refund_decision_accuracy" in score_data:
                    valid_scores.append(score_data["refund_decision_accuracy"])
                elif "reason_quality_score" in score_data:
                    valid_scores.append(score_data["reason_quality_score"])
                elif "refund_fee_accuracy" in score_data:
                    valid_scores.append(score_data["refund_fee_accuracy"])
                elif "policy_compliance_score" in score_data:
                    valid_scores.append(score_data["policy_compliance_score"])
        
        if valid_scores:
            scorer_averages[scorer_name] = sum(valid_scores) / len(valid_scores)
        else:
            scorer_averages[scorer_name] = 0.0
    
    print("\n📊 평균 점수:")
    for scorer_name, avg_score in scorer_averages.items():
        print(f"  - {scorer_name}: {avg_score:.3f}")
    
    return results

async def main():
    """메인 실행 함수"""
    print("🎯 환불 챗봇 평가 시스템")
    print("1. 샘플 평가 (5개)")
    print("2. 전체 평가 (30개)")
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        await run_sample_evaluation(5)
    elif choice == "2":
        await run_comprehensive_evaluation()
    else:
        print("샘플 평가를 실행합니다...")
        await run_sample_evaluation(5)

if __name__ == "__main__":
    asyncio.run(main())
