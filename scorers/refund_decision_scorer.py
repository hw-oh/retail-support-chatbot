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
            평가 결과 딕셔너리 (환불 여부 정확도와 이유 포함)
        """
        response = model_output.get("response", "")
        expected_result = target
        
        if not response.strip():
            return {
                "accuracy": False,
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
            
            # 환불 여부 정확도를 True/False로 평가
            accuracy_score = float(result.get("accuracy", 0.0))
            reason = result.get("reason", "평가 결과를 가져올 수 없습니다.")
            
            # 0.5 이상이면 True, 미만이면 False
            accuracy = accuracy_score >= 0.5
            
            return {
                "accuracy": accuracy,
                "reason": reason
            }
            
        except Exception as e:
            return {
                "accuracy": False,
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

**평가 기준:**
- 결과를 평가할 때 환불 금액 등의 기타 정보는 평가하지 않습니다.
- 오로지 환불 가능 여부 판단이 올바른지만 평가합니다.
- 환불 가능 여부가 정답과 일치하는가?
- 판단 근거가 환불 정책에 따라 타당한가?

**점수 기준:**
- True: 환불 가능 여부를 정확하게 판단함
- False: 환불 가능 여부를 잘못 판단함

**응답 형식 (JSON):**
{{
    "accuracy": True 또는 False,
    "reason": "환불 가능 여부 판단이 정확한지에 대한 구체적인 평가 이유"
}}
"""
        return prompt