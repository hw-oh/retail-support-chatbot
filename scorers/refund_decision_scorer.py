import weave
import re
from typing import Dict, Any

class RefundDecisionScorer(weave.Model):
    """환불 여부 결정 정확도를 평가하는 스코어러"""
    
    def __init__(self):
        pass
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        환불 여부 정확도 평가
        
        Args:
            target: 기대 결과 (expected_result)
            model_output: 모델 출력 (챗봇 응답)
        
        Returns:
            평가 결과 딕셔너리
        """
        expected = target.get("refund_possible")
        predicted = self._extract_refund_decision(model_output.get("response", ""))
        
        if expected is None:
            return {"accuracy": 0.0, "correct": False, "error": "Missing expected refund decision"}
        
        if predicted is None:
            return {"accuracy": 0.0, "correct": False, "error": "Could not determine refund decision from response"}
        
        correct = bool(expected) == bool(predicted)
        return {
            "accuracy": 1.0 if correct else 0.0,
            "correct": correct,
            "expected": expected,
            "predicted": predicted
        }
    
    def _extract_refund_decision(self, response: str) -> bool:
        """응답에서 환불 가능 여부 추출"""
        if not response:
            return None
            
        response_lower = response.lower()
        
        # 환불 불가 키워드 (더 강한 신호)
        reject_keywords = [
            "환불 불가", "환불할 수 없", "환불이 불가능", "환불 거부",
            "취소할 수 없", "취소 불가", "불가합니다", "어렵습니다",
            "환불되지 않습니다", "환불하실 수 없습니다"
        ]
        
        # 환불 가능 키워드  
        accept_keywords = [
            "환불 가능", "환불할 수 있", "환불이 가능", "환불 처리",
            "취소 가능", "취소할 수 있", "무료 취소", "즉시 처리",
            "환불해드리겠습니다", "환불 진행"
        ]
        
        # 거부 키워드 체크 (우선순위 높음)
        reject_count = sum(1 for keyword in reject_keywords if keyword in response_lower)
        accept_count = sum(1 for keyword in accept_keywords if keyword in response_lower)
        
        if reject_count > accept_count:
            return False
        elif accept_count > reject_count:
            return True
        else:
            # 애매한 경우 추가 패턴 체크
            if "하지만" in response_lower or "그러나" in response_lower:
                # 조건부 응답인 경우 문맥 파악
                return None
            return False  # 기본값
