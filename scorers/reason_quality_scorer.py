import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class ReasonQualityScorer(weave.Model):
    """LLM 기반 이유 설명 품질 평가 스코어러"""
    
    model_name: str = config.REASON_QUALITY_MODEL
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """
        LLM을 사용한 이유 설명 품질 평가
        
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
                "reason_score": 0.0,
                "reason": "응답이 비어있습니다."
            }
        
        # LLM을 사용한 이유 설명 품질 평가
        evaluation_prompt = self._create_evaluation_prompt(response, expected_result)
        
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            llm_response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "당신은 챗봇 응답의 추론 품질을 평가하는 전문가입니다. 챗봇이 제공한 이유와 설명의 품질을 평가하세요."},
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
                "reason_score": score,
                "reason": reason
            }
            
        except Exception as e:
            return {
                "reason_score": 0.0,
                "reason": f"LLM 평가 중 오류 발생: {str(e)}"
            }
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict) -> str:
        """이유 설명 품질 평가를 위한 프롬프트 생성"""
        
        prompt = f"""
다음 환불 챗봇 응답의 추론 품질과 설명 품질을 평가해주세요.

**평가 기준:**
1. **논리적 추론**: 환불 가능/불가능 판단의 논리가 명확하고 타당한가?
2. **구체적 설명**: 왜 그런 결정에 도달했는지 구체적으로 설명했는가?
3. **관련 정보 포함**: 환불 기간, 상품 유형, 주문 상태 등 관련 정보를 적절히 언급했는가?
4. **고객 친화적**: 고객이 이해하기 쉽게 설명했는가?
5. **정확성**: 제시한 이유와 정보가 정확한가?
6. **완성도**: 설명이 충분하고 빠뜨린 중요한 정보가 없는가?

**챗봇 응답:**
{response}

**기대 결과 정보:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**평가 요청:**
위 응답의 추론 품질과 설명 품질을 0.0에서 1.0 사이의 점수로 평가하고, 구체적인 이유를 제시해주세요.

**평가 포인트:**
- 논리적 흐름이 자연스러운가?
- 고객이 결정 이유를 명확히 이해할 수 있는가?
- 필요한 정보들이 적절히 포함되어 있는가?
- 설명이 구체적이고 도움이 되는가?

**응답 형식 (JSON):**
{{
    "score": 0.75,
    "reason": "환불 불가 사유를 7일 초과라는 구체적 근거와 함께 명확히 설명했으나, 수수료나 배송비 관련 추가 안내가 부족함. 전반적으로 논리적이고 이해하기 쉬운 설명임."
}}
"""
        return prompt