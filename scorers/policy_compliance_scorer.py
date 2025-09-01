import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class PolicyComplianceScorer(weave.Model):
    """LLM 기반 정책 준수도 평가 스코어러"""
    
    model_name: str = config.POLICY_COMPLIANCE_MODEL
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        LLM을 사용한 정책 준수도 평가
        
        Args:
            target: 기대 결과
            model_output: 모델 출력
        
        Returns:
            평가 결과 딕셔너리 (정확도와 이유 포함)
        """
        response = model_output.get("response", "")
        expected_result = target
        
        if not response.strip():
            return {
                "policy_compliance": 0.0,
                "reason": "응답이 비어있습니다."
            }
        
        # LLM을 사용한 정책 준수도 평가
        evaluation_prompt = self._create_evaluation_prompt(response, expected_result)
        
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            llm_response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "당신은 환불 정책 준수도를 평가하는 전문가입니다. 주어진 챗봇 응답이 환불 정책을 얼마나 잘 준수하는지 평가하세요."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(llm_response.choices[0].message.content)
            score = float(result.get("score", 0.0))
            reason = result.get("reason", "평가 결과를 가져올 수 없습니다.")
            
            # 점수가 0-1 범위를 벗어나면 조정
            score = max(0.0, min(1.0, score))
            
            return {
                "policy_compliance": score,
                "reason": reason
            }
            
        except Exception as e:
            return {
                "policy_compliance": 0.0,
                "reason": f"LLM 평가 중 오류 발생: {str(e)}"
            }
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict) -> str:
        """정책 준수도 평가를 위한 프롬프트 생성"""
        
        # 환불 정책 파일 읽기
        try:
            with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
                refund_policy = f.read()
        except FileNotFoundError:
            refund_policy = "환불 정책 파일을 찾을 수 없습니다."
        
        prompt = f"""
다음 환불 챗봇 응답의 정책 준수도를 평가해주세요.

**환불 정책 기준:**
{refund_policy}

**챗봇 응답:**
{response}

**기대 결과 정보:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**평가 요청:**
위 응답이 환불 정책을 얼마나 잘 준수하는지 0.0에서 1.0 사이의 점수로 평가하고, 구체적인 이유를 제시해주세요.

**응답 형식 (JSON):**
{{
    "score": 0.85,
    "reason": "7일 환불 기간과 10% 수수료 정책을 명확히 언급했으나, 배송비 고객 부담에 대한 언급이 부족함. 전반적으로 정책을 잘 준수하는 응답임."
}}
"""
        return prompt