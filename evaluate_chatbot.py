import json
import weave
import re
from typing import Dict, List, Any
from simple_chatbot import SimplifiedChatbot

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
            
            # 응답에서 환불 관련 정보 추출
            refund_possible = self._extract_refund_decision(response)
            refund_fee = self._extract_refund_fee(response)
            reason = self._extract_reason(response)
            
            return {
                "response": response,
                "refund_possible": refund_possible,
                "refund_fee": refund_fee,
                "reason": reason,
                "raw_response": response
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "refund_possible": None,
                "refund_fee": None,
                "reason": f"Error occurred: {str(e)}",
                "raw_response": f"Error: {str(e)}"
            }
    
    def _extract_refund_decision(self, response: str) -> bool:
        """응답에서 환불 가능 여부 추출"""
        response_lower = response.lower()
        
        # 환불 불가 키워드
        reject_keywords = [
            "환불 불가", "환불할 수 없", "환불이 불가능", "환불 거부",
            "취소할 수 없", "취소 불가", "불가합니다", "어렵습니다"
        ]
        
        # 환불 가능 키워드  
        accept_keywords = [
            "환불 가능", "환불할 수 있", "환불이 가능", "환불 처리",
            "취소 가능", "취소할 수 있", "무료 취소", "즉시 처리"
        ]
        
        # 불가 키워드가 있으면 False
        for keyword in reject_keywords:
            if keyword in response_lower:
                return False
        
        # 가능 키워드가 있으면 True
        for keyword in accept_keywords:
            if keyword in response_lower:
                return True
                
        # 애매한 경우 None 반환하지만 여기서는 False로 처리
        return False
    
    def _extract_refund_fee(self, response: str) -> int:
        """응답에서 환불 수수료 추출"""
        # 수수료 관련 패턴
        fee_patterns = [
            r'(\d+,?\d*)\s*원.*수수료',
            r'수수료.*?(\d+,?\d*)\s*원',
            r'환불.*?(\d+,?\d*)\s*원.*차감',
            r'(\d+,?\d*)\s*원.*차감',
            r'최소.*?(\d+,?\d*)\s*원'
        ]
        
        for pattern in fee_patterns:
            matches = re.findall(pattern, response)
            if matches:
                # 쉼표 제거 후 숫자로 변환
                fee_str = matches[0].replace(',', '')
                try:
                    return int(fee_str)
                except ValueError:
                    continue
        
        # 무료 취소/환불인 경우
        if any(keyword in response.lower() for keyword in ["무료", "수수료 없음", "수수료는 없"]):
            return 0
            
        return None
    
    def _extract_reason(self, response: str) -> str:
        """응답에서 환불 사유 추출"""
        # 주요 키워드로 간단한 사유 분류
        reason_keywords = {
            "7일 이내": ["7일 이내", "환불 기간"],
            "7일 초과": ["7일 초과", "기간이 지나"],
            "개인위생용품": ["개인위생용품", "화장품", "향수"],
            "배송 전": ["배송 전", "상품준비중", "주문접수", "결제완료"],
            "배송 중": ["배송 중", "배송중"],
            "불량품": ["불량품", "파손", "변질"],
            "존재하지 않는 주문": ["주문 정보", "확인할 수 없", "존재하지 않"]
        }
        
        response_lower = response.lower()
        for reason, keywords in reason_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                return reason
        
        return "기타"

# 평가 함수들 정의
@weave.op()
def refund_decision_accuracy(target: Dict, output: Dict) -> Dict[str, Any]:
    """환불 여부 정확도 평가"""
    expected = target.get("refund_possible")
    predicted = output.get("refund_possible")
    
    if expected is None or predicted is None:
        return {"accuracy": 0.0, "correct": False, "error": "Missing refund decision"}
    
    correct = bool(expected) == bool(predicted)
    return {
        "accuracy": 1.0 if correct else 0.0,
        "correct": correct,
        "expected": expected,
        "predicted": predicted
    }

@weave.op()
def reason_quality_score(target: Dict, output: Dict) -> Dict[str, Any]:
    """이유 설명 품질 평가"""
    expected_reason = target.get("reason", "")
    response = output.get("response", "")
    
    # 키워드 기반 평가
    key_concepts = {
        "시간": ["7일", "기간", "날짜"],
        "정책": ["정책", "규정", "원칙"],
        "상품유형": ["개인위생용품", "화장품", "불량품"],
        "상태": ["배송", "주문", "상태"]
    }
    
    score = 0.0
    concept_scores = {}
    
    response_lower = response.lower()
    for concept, keywords in key_concepts.items():
        found = any(keyword in response_lower for keyword in keywords)
        concept_scores[concept] = 1.0 if found else 0.0
        score += concept_scores[concept]
    
    # 정규화 (0-1 사이)
    normalized_score = score / len(key_concepts)
    
    return {
        "reason_score": normalized_score,
        "concept_scores": concept_scores,
        "has_explanation": len(response.strip()) > 50
    }

@weave.op()
def refund_fee_accuracy(target: Dict, output: Dict) -> Dict[str, Any]:
    """환불 수수료 계산 정확도 평가"""
    expected_fee = target.get("refund_fee")
    predicted_fee = output.get("refund_fee")
    
    if expected_fee is None:
        return {"fee_accuracy": 1.0 if predicted_fee is None else 0.0, "correct": True}
    
    if predicted_fee is None:
        return {"fee_accuracy": 0.0, "correct": False, "error": "No fee extracted"}
    
    # 정확한 금액 매치
    exact_match = expected_fee == predicted_fee
    
    # 허용 오차 (±10%)
    if expected_fee > 0:
        tolerance = max(200, expected_fee * 0.1)  # 최소 200원 또는 10% 오차
        within_tolerance = abs(expected_fee - predicted_fee) <= tolerance
    else:
        within_tolerance = predicted_fee == 0
    
    return {
        "fee_accuracy": 1.0 if exact_match else (0.7 if within_tolerance else 0.0),
        "exact_match": exact_match,
        "within_tolerance": within_tolerance,
        "expected_fee": expected_fee,
        "predicted_fee": predicted_fee,
        "difference": abs(expected_fee - predicted_fee) if predicted_fee is not None else None
    }

@weave.op()
def policy_compliance_score(target: Dict, output: Dict) -> Dict[str, Any]:
    """정책 준수도 평가"""
    response = output.get("response", "").lower()
    expected_result = target.get("expected_result", {})
    
    # 정책 준수 체크리스트
    compliance_checks = {
        "mentions_timeframe": any(term in response for term in ["7일", "기간", "시간"]),
        "mentions_fee_policy": any(term in response for term in ["수수료", "10%", "2,000원", "최소"]),
        "mentions_shipping_cost": any(term in response for term in ["배송비", "고객 부담", "왕복"]),
        "mentions_hygiene_products": any(term in response for term in ["개인위생용품", "화장품", "향수"]),
        "mentions_defective_exception": any(term in response for term in ["불량품", "파손", "변질"]) if "불량품" in str(expected_result) else True
    }
    
    # 정책 위반 체크 (잘못된 정보 제공)
    violations = {
        "wrong_timeframe": any(term in response for term in ["14일", "30일", "한달"]),
        "wrong_fee_info": any(term in response for term in ["수수료 없음"]) and expected_result.get("refund_fee", 0) > 0,
    }
    
    compliance_score = sum(compliance_checks.values()) / len(compliance_checks)
    violation_penalty = sum(violations.values()) * 0.2  # 위반당 20% 감점
    
    final_score = max(0.0, compliance_score - violation_penalty)
    
    return {
        "policy_compliance": final_score,
        "compliance_checks": compliance_checks,
        "violations": violations,
        "compliance_rate": compliance_score
    }

def load_evaluation_dataset():
    """평가 데이터셋 로드"""
    with open('data/evaluate_refund.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Weave Evaluation 형식으로 변환
    examples = []
    for item in data:
        example = {
            "id": item["test_id"],
            "user_query": item["user_query"],
            "order_info": item["order_info"],
            "scenario": item["scenario"],
            "target": item["expected_result"]
        }
        examples.append(example)
    
    return examples

async def main():
    # Weave 초기화
    weave.init('retail-chatbot-dev')
    
    # 모델 생성
    model = RefundChatbotModel()
    
    # 데이터셋 로드
    examples = load_evaluation_dataset()
    print(f"📊 {len(examples)}개의 테스트 시나리오 로드됨")
    
    # 평가 설정
    evaluation = weave.Evaluation(
        name="refund_chatbot_evaluation",
        dataset=examples,
        scorers=[
            refund_decision_accuracy,
            reason_quality_score, 
            refund_fee_accuracy,
            policy_compliance_score
        ]
    )
    
    print("🚀 환불 챗봇 평가 시작...")
    
    # 평가 실행
    results = await evaluation.evaluate(model)
    
    print("✅ 평가 완료!")
    print(f"📈 결과: {results}")
    
    return results

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
