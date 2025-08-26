import weave
import re
from typing import Dict, Any, Optional

# 환불 여부 결정 정확도 평가
@weave.op()
def refund_decision_accuracy(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """환불 여부 정확도 평가"""
    expected = expected_result.get("refund_possible")
    predicted = _extract_refund_decision(output.get("response", ""))
    
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

def _extract_refund_decision(response: str) -> bool:
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

# 이유 설명 품질 평가
@weave.op()
def reason_quality_score(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """이유 설명 품질 평가"""
    
    # 핵심 개념별 키워드 정의
    key_concepts = {
        "시간_정책": ["7일", "기간", "날짜", "시간", "언제", "경과"],
        "환불_정책": ["정책", "규정", "원칙", "수수료", "10%", "2,000원"],
        "상품_유형": ["개인위생용품", "화장품", "불량품", "파손", "변질"],
        "주문_상태": ["배송", "주문", "상태", "준비중", "접수", "완료"],
        "배송비_정책": ["배송비", "고객 부담", "왕복", "추가 비용"]
    }
    
    response = output.get("response", "")
    
    if not response.strip():
        return {
            "reason_score": 0.0,
            "concept_scores": {},
            "has_explanation": False,
            "response_length": 0
        }
    
    response_lower = response.lower()
    
    # 개념별 점수 계산
    concept_scores = {}
    total_score = 0.0
    
    for concept, keywords in key_concepts.items():
        found_keywords = [kw for kw in keywords if kw in response_lower]
        concept_score = min(1.0, len(found_keywords) * 0.5)  # 키워드당 0.5점, 최대 1.0
        concept_scores[concept] = {
            "score": concept_score,
            "found_keywords": found_keywords
        }
        total_score += concept_score
    
    # 정규화 (0-1 사이)
    max_possible_score = len(key_concepts)
    normalized_score = total_score / max_possible_score
    
    # 추가 품질 지표
    response_length = len(response.strip())
    has_detailed_explanation = response_length > 100
    has_structured_info = any(marker in response for marker in ["1.", "2.", "-", "•"])
    has_specific_amounts = any(char.isdigit() for char in response)
    
    # 보너스 점수
    bonus = 0.0
    if has_detailed_explanation:
        bonus += 0.1
    if has_structured_info:
        bonus += 0.1
    if has_specific_amounts:
        bonus += 0.1
    
    final_score = min(1.0, normalized_score + bonus)
    
    return {
        "reason_score": final_score,
        "concept_scores": concept_scores,
        "has_explanation": response_length > 50,
        "has_detailed_explanation": has_detailed_explanation,
        "has_structured_info": has_structured_info,
        "has_specific_amounts": has_specific_amounts,
        "response_length": response_length,
        "bonus_score": bonus
    }

# 환불 수수료 계산 정확도 평가
@weave.op()
def refund_fee_accuracy(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """환불 수수료 계산 정확도 평가"""
    expected_fee = expected_result.get("refund_fee")
    response = output.get("response", "")
    predicted_fee = _extract_refund_fee(response)
    
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

def _extract_refund_fee(response: str) -> Optional[int]:
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

# 정책 준수도 평가
@weave.op()
def policy_compliance_score(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """정책 준수도 평가"""
    
    # 정책 준수 체크리스트
    compliance_rules = {
        "time_policy": {
            "keywords": ["7일", "기간", "시간"],
            "description": "7일 환불 기간 정책 언급"
        },
        "fee_policy": {
            "keywords": ["수수료", "10%", "2,000원", "최소"],
            "description": "환불 수수료 정책 언급"
        },
        "shipping_cost": {
            "keywords": ["배송비", "고객 부담", "왕복"],
            "description": "배송비 고객 부담 정책 언급"
        },
        "hygiene_products": {
            "keywords": ["개인위생용품", "화장품", "향수"],
            "description": "개인위생용품 환불 제한 정책 언급"
        },
        "defective_exception": {
            "keywords": ["불량품", "파손", "변질", "결함"],
            "description": "불량품 예외 조건 언급"
        },
        "processing_time": {
            "keywords": ["3-5일", "영업일", "처리 기간"],
            "description": "환불 처리 기간 언급"
        }
    }
    
    # 정책 위반 체크리스트 (잘못된 정보)
    violation_rules = {
        "wrong_timeframe": {
            "keywords": ["14일", "30일", "한달", "2주"],
            "penalty": 0.3,
            "description": "잘못된 환불 기간 제시"
        },
        "wrong_fee_info": {
            "keywords": ["수수료 없음", "무료 환불"],
            "penalty": 0.2,
            "description": "잘못된 수수료 정보 (수수료 있는 경우)"
        },
        "wrong_shipping_info": {
            "keywords": ["배송비 무료", "배송비 지원"],
            "penalty": 0.1,
            "description": "잘못된 배송비 정보"
        }
    }
    
    response = output.get("response", "")
    # expected_result는 이미 매개변수로 전달됨
    
    if not response.strip():
        return {
            "policy_compliance": 0.0,
            "compliance_checks": {},
            "violations": {},
            "error": "Empty response"
        }
    
    response_lower = response.lower()
    
    # 준수 사항 체크
    compliance_checks = {}
    compliance_score = 0.0
    
    for rule_name, rule_info in compliance_rules.items():
        found_keywords = [kw for kw in rule_info["keywords"] if kw in response_lower]
        is_compliant = len(found_keywords) > 0
        
        # 특별한 경우 처리
        if rule_name == "defective_exception":
            # 불량품 관련 시나리오가 아닌 경우 체크하지 않음
            if "불량품" not in str(expected_result) and "파손" not in str(expected_result):
                is_compliant = True  # 해당 없음으로 처리
        
        compliance_checks[rule_name] = {
            "compliant": is_compliant,
            "found_keywords": found_keywords,
            "description": rule_info["description"]
        }
        
        if is_compliant:
            compliance_score += 1.0
    
    # 정규화
    max_compliance_score = len(compliance_rules)
    normalized_compliance = compliance_score / max_compliance_score
    
    # 위반 사항 체크
    violations = {}
    total_penalty = 0.0
    
    for violation_name, violation_info in violation_rules.items():
        found_violations = [kw for kw in violation_info["keywords"] if kw in response_lower]
        has_violation = len(found_violations) > 0
        
        # 컨텍스트별 위반 체크
        if violation_name == "wrong_fee_info":
            expected_fee = expected_result.get("refund_fee", 0)
            if expected_fee is not None and expected_fee > 0 and has_violation:
                # 수수료가 있어야 하는데 무료라고 잘못 안내
                total_penalty += violation_info["penalty"]
            else:
                has_violation = False
        elif has_violation:
            total_penalty += violation_info["penalty"]
        
        violations[violation_name] = {
            "violated": has_violation,
            "found_violations": found_violations,
            "penalty": violation_info["penalty"] if has_violation else 0.0,
            "description": violation_info["description"]
        }
    
    # 최종 점수 계산
    final_score = max(0.0, normalized_compliance - total_penalty)
    
    # 추가 점수: 명확하고 구체적인 안내
    bonus = 0.0
    if "안내" in response_lower or "도움" in response_lower:
        bonus += 0.05
    if any(marker in response for marker in ["1.", "2.", "3.", "-", "•"]):
        bonus += 0.05
    
    final_score = min(1.0, final_score + bonus)
    
    return {
        "policy_compliance": final_score,
        "compliance_score": normalized_compliance,
        "compliance_checks": compliance_checks,
        "violations": violations,
        "total_penalty": total_penalty,
        "bonus_score": bonus,
        "detailed_guidance": len(response) > 200
    }
