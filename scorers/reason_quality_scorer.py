import weave
from typing import Dict, Any

class ReasonQualityScorer(weave.Model):
    """이유 설명 품질을 평가하는 스코어러"""
    
    # 핵심 개념별 키워드 정의 (클래스 레벨에서 정의)
    key_concepts: dict = {
            "시간_정책": ["7일", "기간", "날짜", "시간", "언제", "경과"],
            "환불_정책": ["정책", "규정", "원칙", "수수료", "10%", "2,000원"],
            "상품_유형": ["개인위생용품", "화장품", "불량품", "파손", "변질"],
            "주문_상태": ["배송", "주문", "상태", "준비중", "접수", "완료"],
            "배송비_정책": ["배송비", "고객 부담", "왕복", "추가 비용"]
        }
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        이유 설명 품질 평가
        
        Args:
            target: 기대 결과
            model_output: 모델 출력
        
        Returns:
            평가 결과 딕셔너리
        """
        response = model_output.get("response", "")
        expected_reason = target.get("reason", "")
        
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
        
        for concept, keywords in self.key_concepts.items():
            found_keywords = [kw for kw in keywords if kw in response_lower]
            concept_score = min(1.0, len(found_keywords) * 0.5)  # 키워드당 0.5점, 최대 1.0
            concept_scores[concept] = {
                "score": concept_score,
                "found_keywords": found_keywords
            }
            total_score += concept_score
        
        # 정규화 (0-1 사이)
        max_possible_score = len(self.key_concepts)
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
