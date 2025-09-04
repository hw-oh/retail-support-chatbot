import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class ReasonQualityScorer(weave.Model):
    """LLM-based reason explanation quality evaluation scorer with multi-language support"""
    
    model_name: str = config.REASON_QUALITY_MODEL
    language: str = "ko"  # Default language
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict, language: str = "ko") -> Dict[str, Any]:
        """
        LLM-based reason explanation quality evaluation
        
        Args:
            target: Expected result
            model_output: Model output
            language: Language for evaluation (ko, en, jp)
        
        Returns:
            Evaluation result dictionary (accuracy and reason included)
        """
        self.language = language
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
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict, language: str = "ko") -> str:
        """Generate prompt for reason explanation quality evaluation"""
        
        prompts = {
            "ko": f"""
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
""",
            "en": f"""
Please evaluate the reasoning quality and explanation quality of the following refund chatbot response.

**Evaluation Criteria:**
1. **Logical Reasoning**: Is the logic for refund possible/impossible judgment clear and valid?
2. **Specific Explanation**: Did it specifically explain why it reached that decision?
3. **Relevant Information Included**: Did it appropriately mention relevant information such as refund period, product type, order status, etc.?
4. **Customer-Friendly**: Did it explain in a way that customers can easily understand?
5. **Accuracy**: Are the reasons and information provided accurate?
6. **Completeness**: Is the explanation sufficient and are there no missing important information?

**Chatbot Response:**
{response}

**Expected Result Information:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**Evaluation Request:**
Evaluate the reasoning quality and explanation quality of the above response on a scale of 0.0 to 1.0, and provide specific reasons.

**Evaluation Points:**
- Is the logical flow natural?
- Can customers clearly understand the decision reasons?
- Are necessary information appropriately included?
- Is the explanation specific and helpful?

**Response Format (JSON):**
{{
    "score": 0.75,
    "reason": "Clearly explained the reason for refund rejection with specific basis of exceeding 7 days, but lacks additional guidance on fees or shipping costs. Overall, it's a logical and easy-to-understand explanation."
}}
""",
            "jp": f"""
以下の返品チャットボットの応答の推論品質と説明品質を評価してください。

**評価基準:**
1. **論理的推論**: 返品可能・不可能の判断の論理が明確で妥当か？
2. **具体的説明**: なぜその決定に達したのか具体的に説明したか？
3. **関連情報の含有**: 返品期間、商品タイプ、注文状態などの関連情報を適切に言及したか？
4. **顧客フレンドリー**: 顧客が理解しやすいように説明したか？
5. **正確性**: 提示した理由と情報が正確か？
6. **完成度**: 説明が十分で重要な情報の漏れがないか？

**チャットボットの応答:**
{response}

**期待結果情報:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**評価リクエスト:**
上記の応答の推論品質と説明品質を0.0から1.0のスコアで評価し、具体的な理由を提示してください。

**評価ポイント:**
- 論理的な流れが自然か？
- 顧客が決定理由を明確に理解できるか？
- 必要な情報が適切に含まれているか？
- 説明が具体的で役に立つか？

**応答形式 (JSON):**
{{
    "score": 0.75,
    "reason": "返品不可理由を7日超過という具体的根拠とともに明確に説明しましたが、手数料や送料関連の追加案内が不足しています。全体的に論理的で理解しやすい説明です。"
}}
"""
        }
        
        prompt = prompts.get(self.language, prompts["ko"])
        return prompt
    
    # Convenience methods for different languages
    def score_ko(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """Korean evaluation"""
        return self.score(target, model_output, "ko")
    
    def score_en(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """English evaluation"""
        return self.score(target, model_output, "en")
    
    def score_jp(self, target: Dict, model_output: Dict) -> Dict[str, Any]:
        """Japanese evaluation"""
        return self.score(target, model_output, "jp")