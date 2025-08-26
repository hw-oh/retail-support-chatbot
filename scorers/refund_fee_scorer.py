import weave
import re
from typing import Dict, Any, Optional

class RefundFeeScorer(weave.Model):
    """환불 수수료 계산 정확도를 평가하는 스코어러"""
    
    def __init__(self):
        pass
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        환불 수수료 계산 정확도 평가
        
        Args:
            target: 기대 결과
            model_output: 모델 출력
        
        Returns:
            평가 결과 딕셔너리
        """
        expected_fee = target.get("refund_fee")
        response = model_output.get("response", "")
        predicted_fee = self._extract_refund_fee(response)
        
        # 환불 불가능한 경우 (수수료가 None이어야 함)
        if expected_fee is None:
            if predicted_fee is None:
                return {
                    "fee_accuracy": 1.0,
                    "correct": True,
                    "expected_fee": None,
                    "predicted_fee": None,
                    "note": "Correctly identified no fee (refund not possible)"
                }
            else:
                return {
                    "fee_accuracy": 0.0,
                    "correct": False,
                    "expected_fee": None,
                    "predicted_fee": predicted_fee,
                    "error": "Extracted fee when none should exist"
                }
        
        # 수수료 추출 실패
        if predicted_fee is None:
            return {
                "fee_accuracy": 0.0,
                "correct": False,
                "expected_fee": expected_fee,
                "predicted_fee": None,
                "error": "Could not extract fee from response"
            }
        
        # 정확한 금액 매치
        exact_match = expected_fee == predicted_fee
        
        # 허용 오차 계산
        if expected_fee > 0:
            tolerance = max(500, expected_fee * 0.15)  # 최소 500원 또는 15% 오차
            within_tolerance = abs(expected_fee - predicted_fee) <= tolerance
        else:
            within_tolerance = predicted_fee == 0
        
        # 점수 계산
        if exact_match:
            accuracy = 1.0
        elif within_tolerance:
            accuracy = 0.7
        else:
            # 완전히 틀린 경우에도 범위에 따라 부분 점수
            error_ratio = abs(expected_fee - predicted_fee) / max(expected_fee, 1)
            if error_ratio < 0.5:  # 50% 오차 이내
                accuracy = 0.3
            else:
                accuracy = 0.0
        
        return {
            "fee_accuracy": accuracy,
            "exact_match": exact_match,
            "within_tolerance": within_tolerance,
            "expected_fee": expected_fee,
            "predicted_fee": predicted_fee,
            "difference": abs(expected_fee - predicted_fee),
            "error_ratio": abs(expected_fee - predicted_fee) / max(expected_fee, 1)
        }
    
    def _extract_refund_fee(self, response: str) -> Optional[int]:
        """응답에서 환불 수수료 추출"""
        if not response:
            return None
            
        # 무료 취소/환불 키워드 체크
        free_keywords = ["무료", "수수료 없음", "수수료는 없", "0원", "무료로"]
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in free_keywords):
            return 0
        
        # 수수료 관련 패턴들 (우선순위 순)
        fee_patterns = [
            # 명시적 수수료 언급
            r'수수료.*?(\d+,?\d*)\s*원',
            r'(\d+,?\d*)\s*원.*수수료',
            
            # 환불 금액에서 차감
            r'환불.*?(\d+,?\d*)\s*원.*차감',
            r'(\d+,?\d*)\s*원.*차감',
            
            # 최소 수수료
            r'최소.*?(\d+,?\d*)\s*원',
            
            # 10% 언급과 함께 나오는 금액
            r'10%.*?(\d+,?\d*)\s*원',
            r'(\d+,?\d*)\s*원.*10%',
            
            # 기본 패턴: 숫자 + 원
            r'(\d+,?\d*)\s*원'
        ]
        
        for pattern in fee_patterns:
            matches = re.findall(pattern, response)
            if matches:
                for match in matches:
                    # 쉼표 제거 후 숫자로 변환
                    fee_str = match.replace(',', '')
                    try:
                        fee = int(fee_str)
                        # 합리적인 수수료 범위 체크 (0원 ~ 100만원)
                        if 0 <= fee <= 1000000:
                            # 너무 큰 금액은 상품 가격일 가능성이 높음
                            if fee > 50000:
                                continue
                            return fee
                    except ValueError:
                        continue
        
        return None
