import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class RefundDecisionScorer(weave.Model):
    """LLM-based refund decision accuracy evaluation scorer with multi-language support"""
    
    model_name: str = config.REFUND_DECISION_MODEL
    language: str = "ko"  # Default language
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict, language: str = "ko") -> Dict[str, Any]:
        """
        LLM-based refund decision accuracy evaluation
        
        Args:
            target: Expected result (expected_result)
            model_output: Model output (chatbot response)
            language: Language for evaluation (ko, en, jp)
        
        Returns:
            Evaluation result dictionary (refund decision accuracy and reason included)
        """
        self.language = language
        response = model_output.get("response", "")
        expected_result = target
        
        if not response.strip():
            empty_msg = {
                "ko": "응답이 비어있습니다.",
                "en": "Response is empty.",
                "jp": "応答が空です。"
            }
            return {
                "accuracy": False,
                "reason": empty_msg.get(language, empty_msg["ko"])
            }
        
        # LLM-based refund decision evaluation
        evaluation_prompt = self._create_evaluation_prompt(response, expected_result, language)
        
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            system_messages = {
                "ko": "당신은 환불 여부 결정의 정확성을 평가하는 전문가입니다. 챗봇의 환불 가능/불가능 판단이 올바른지 평가하세요.",
                "en": "You are an expert evaluating the accuracy of refund decisions. Evaluate whether the chatbot's refund possible/impossible judgment is correct.",
                "jp": "あなたは返品判定の正確性を評価する専門家です。チャットボットの返品可能・不可能の判断が正しいか評価してください。"
            }
            
            llm_response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_messages.get(language, system_messages["ko"])},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(llm_response.choices[0].message.content)
            
            # 환불 여부 정확도를 True/False로 평가
            accuracy_score = float(result.get("accuracy", 0.0))
            default_reasons = {
                "ko": "평가 결과를 가져올 수 없습니다.",
                "en": "Cannot retrieve evaluation result.",
                "jp": "評価結果を取得できません。"
            }
            reason = result.get("reason", default_reasons.get(language, default_reasons["ko"]))
            
            # 0.5 이상이면 True, 미만이면 False
            accuracy = accuracy_score >= 0.5
            
            return {
                "accuracy": accuracy,
                "reason": reason
            }
            
        except Exception as e:
            error_msgs = {
                "ko": f"LLM 평가 중 오류 발생: {str(e)}",
                "en": f"Error during LLM evaluation: {str(e)}",
                "jp": f"LLM評価中にエラーが発生しました: {str(e)}"
            }
            return {
                "accuracy": False,
                "reason": error_msgs.get(language, error_msgs["ko"])
            }
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict, language: str = "ko") -> str:
        """Generate prompt for refund decision accuracy evaluation"""
        
        expected_refund = expected_result.get("refund_possible", None)
        expected_reason = expected_result.get("reason", "")
        
        # Load refund policy file based on language
        try:
            policy_path = config.get_data_path('refund_policy.txt', language)
            with open(policy_path, 'r', encoding='utf-8') as f:
                refund_policy = f.read()
        except FileNotFoundError:
            # Fallback to Korean policy
            with open('data/ko/refund_policy.txt', 'r', encoding='utf-8') as f:
                refund_policy = f.read()
            
        prompts = {
            "ko": f"""
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

**점수 기준:**
- True: 환불 가능 여부를 정확하게 판단함
- False: 환불 가능 여부를 잘못 판단함

**응답 형식 (JSON):**
{{
    "accuracy": True 또는 False,
    "reason": "환불 가능 여부 판단이 정확한지에 대한 구체적인 평가 이유"
}}
""",
            "en": f"""
Please evaluate whether the refund chatbot response correctly determines refund eligibility.

**Chatbot Response:**
{response}

**Correct Answer Information:**
- Refund Possible: {expected_refund}
- Expected Reason: {expected_reason}

**Evaluation Criteria:**
- When evaluating results, do not evaluate other information such as refund amount.
- Only evaluate whether the refund eligibility judgment is correct.
- Does the refund eligibility match the correct answer?

**Scoring Criteria:**
- True: Correctly determined refund eligibility
- False: Incorrectly determined refund eligibility

**Response Format (JSON):**
{{
    "accuracy": True or False,
    "reason": "Specific evaluation reason for whether refund eligibility determination is accurate"
}}
""",
            "jp": f"""
以下の返品チャットボットの応答の返品可能性の判断が正しいか評価してください。

**チャットボットの応答:**
{response}

**正解情報:**
- 返品可能性: {expected_refund}
- 予想理由: {expected_reason}

**評価基準:**
- 結果を評価する際、返品金額などのその他の情報は評価しません。
- 返品可能性の判断が正しいかどうかのみ評価します。
- 返品可能性が正解と一致していますか？

**スコア基準:**
- True: 返品可能性を正確に判断した
- False: 返品可能性を誤って判断した

**応答形式 (JSON):**
{{
    "accuracy": TrueまたはFalse,
    "reason": "返品可能性の判断が正確かどうかについての具体的な評価理由"
}}
"""
        }
        
        prompt = prompts.get(language, prompts["ko"])
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