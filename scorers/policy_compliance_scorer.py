import weave
from typing import Dict, Any

class PolicyComplianceScorer(weave.Model):
    """정책 준수도를 평가하는 스코어러"""
    
    # 정책 준수 체크리스트 (클래스 레벨에서 정의)
    compliance_rules: dict = {
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
    
    # 정책 위반 체크리스트 (클래스 레벨에서 정의)
    violation_rules: dict = {
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
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        정책 준수도 평가
        
        Args:
            target: 기대 결과
            model_output: 모델 출력
        
        Returns:
            평가 결과 딕셔너리
        """
        response = model_output.get("response", "")
        expected_result = target
        
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
        
        for rule_name, rule_info in self.compliance_rules.items():
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
        max_compliance_score = len(self.compliance_rules)
        normalized_compliance = compliance_score / max_compliance_score
        
        # 위반 사항 체크
        violations = {}
        total_penalty = 0.0
        
        for violation_name, violation_info in self.violation_rules.items():
            found_violations = [kw for kw in violation_info["keywords"] if kw in response_lower]
            has_violation = len(found_violations) > 0
            
            # 컨텍스트별 위반 체크
            if violation_name == "wrong_fee_info":
                expected_fee = expected_result.get("refund_fee", 0)
                if expected_fee > 0 and has_violation:
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
