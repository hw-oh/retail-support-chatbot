import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class RefundDecisionScorer(weave.Model):
    """LLM 기반 환불 여부 결정 정확도를 평가하는 스코어러"""
    
    model_name: str = config.REFUND_DECISION_MODEL
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        LLM을 사용한 환불 여부 정확도 평가
        
        Args:
            target: 기대 결과 (expected_result)
            model_output: 모델 출력 (챗봇 응답)
        
        Returns:
            평가 결과 딕셔너리 (정확도와 이유 포함)
        """
        response = model_output.get("response", "")
        expected_result = target
        
        if not response.strip():
            return {
                "accuracy": 0.0,
                "reason": "응답이 비어있습니다."
            }
        
        # LLM을 사용한 환불 결정 평가
        evaluation_prompt = self._create_evaluation_prompt(response, expected_result)
        
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            llm_response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "당신은 환불 여부 결정의 정확성을 평가하는 전문가입니다. 챗봇의 환불 가능/불가능 판단이 올바른지 평가하세요."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(llm_response.choices[0].message.content)
            accuracy = float(result.get("accuracy", 0.0))
            reason = result.get("reason", "평가 결과를 가져올 수 없습니다.")
            
            # 정확도가 0-1 범위를 벗어나면 조정
            accuracy = max(0.0, min(1.0, accuracy))
            
            return {
                "accuracy": accuracy,
                "reason": reason
            }
            
        except Exception as e:
            return {
                "accuracy": 0.0,
                "reason": f"LLM 평가 중 오류 발생: {str(e)}"
            }
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict) -> str:
        """환불 결정 정확도 평가를 위한 프롬프트 생성"""
        
        expected_refund = expected_result.get("refund_possible", None)
        expected_reason = expected_result.get("reason", "")
        with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
            refund_policy = f.read()
        prompt = f"""
다음 환불 챗봇 응답의 환불 가능 여부 판단이 올바른지 평가해주세요.

**챗봇 응답:**
{response}

**정답 정보:**
- 환불 가능 여부: {expected_refund}
- 예상 이유: {expected_reason}

**환불 정책:**
{refund_policy}

**평가 기준:**
1. **환불 가능 여부 정확성**: 챗봇이 환불 가능/불가능을 올바르게 판단했는가?
2. **판단 근거의 타당성**: 환불 결정의 이유가 적절하고 정확한가?
3. **정책 적용의 정확성**: 환불 정책을 올바르게 적용했는가?
4. **일관성**: 응답 전체가 일관된 결론을 제시하는가?

**평가 요청:**
위 응답에서 환불 가능 여부 판단이 얼마나 정확한지 0.0에서 1.0 사이의 점수로 평가하고, 구체적인 이유를 제시해주세요.

**점수 기준:**
- 1.0: 환불 가능 여부와 이유가 모두 정확함
- 0.8: 환불 가능 여부는 정확하나 이유가 일부 부정확함
- 0.6: 환불 가능 여부는 정확하나 이유가 많이 부정확함
- 0.4: 환불 가능 여부가 부정확하나 부분적으로 타당한 근거가 있음
- 0.2: 환불 가능 여부가 부정확하고 근거도 부적절함
- 0.0: 완전히 잘못된 판단이거나 응답이 부적절함

**응답 형식 예시(JSON):**
{{
    "accuracy": 0.85,
    "reason": "환불 가능 여부는 정확하게 판단함. 전반적으로 정책을 잘 적용한 응답임."
}}
"""
        return prompt
