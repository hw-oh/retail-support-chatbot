import json
import weave
import asyncio
from evaluate_chatbot import RefundChatbotModel, refund_decision_accuracy, reason_quality_score, refund_fee_accuracy, policy_compliance_score

async def test_small_evaluation():
    # Weave 초기화
    weave.init('retail-chatbot-dev')
    
    # 모델 생성
    model = RefundChatbotModel()
    
    # 작은 테스트 데이터셋 (처음 3개)
    with open('data/evaluate_refund.json', 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    # 처음 3개만 테스트
    test_data = all_data[:3]
    
    examples = []
    for item in test_data:
        example = {
            "id": item["test_id"],
            "user_query": item["user_query"],
            "order_info": item["order_info"],
            "scenario": item["scenario"],
            "target": item["expected_result"]
        }
        examples.append(example)
    
    print(f"📊 {len(examples)}개의 테스트 시나리오로 시작...")
    
    # 개별 테스트 실행
    for example in examples:
        print(f"\n🧪 테스트: {example['id']} - {example['scenario']}")
        print(f"👤 질문: {example['user_query']}")
        
        # 모델 예측
        result = model.predict(example['user_query'], example['order_info'])
        print(f"🤖 응답: {result['response'][:100]}...")
        
        # 각 평가 함수 실행
        accuracy = refund_decision_accuracy(example['target'], result)
        reason = reason_quality_score(example['target'], result)
        fee = refund_fee_accuracy(example['target'], result)
        compliance = policy_compliance_score(example['target'], result)
        
        print(f"📊 평가 결과:")
        print(f"  - 환불 여부 정확도: {accuracy['accuracy']:.2f}")
        print(f"  - 이유 설명 품질: {reason['reason_score']:.2f}")
        print(f"  - 수수료 정확도: {fee['fee_accuracy']:.2f}")
        print(f"  - 정책 준수도: {compliance['policy_compliance']:.2f}")
    
    print("\n✅ 작은 규모 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_small_evaluation())
