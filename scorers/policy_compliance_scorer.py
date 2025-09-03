import weave
import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class PolicyComplianceScorer(weave.Model):
    """LLM-based policy compliance evaluation scorer with multi-language support"""
    
    model_name: str = config.POLICY_COMPLIANCE_MODEL
    language: str = "ko"  # Default language
    
    @weave.op()
    def score(self, target: Dict, model_output: Dict, language: str = "ko") -> Dict[str, Any]:
        """
        LLM-based policy compliance evaluation
        
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
            empty_msg = {
                "ko": "응답이 비어있습니다.",
                "en": "Response is empty.",
                "jp": "応答が空です。"
            }
            return {
                "policy_compliance": 0.0,
                "reason": empty_msg.get(language, empty_msg["ko"])
            }
        
        # LLM-based policy compliance evaluation
        evaluation_prompt = self._create_evaluation_prompt(response, expected_result, language)
        
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            system_messages = {
                "ko": "당신은 환불 정책 준수도를 평가하는 전문가입니다. 주어진 챗봇 응답이 환불 정책을 얼마나 잘 준수하는지 평가하세요.",
                "en": "You are an expert evaluating refund policy compliance. Evaluate how well the given chatbot response complies with the refund policy.",
                "jp": "あなたは返品ポリシーの遵守度を評価する専門家です。与えられたチャットボットの応答が返品ポリシーをどれだけよく遵守しているか評価してください。"
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
            score = float(result.get("score", 0.0))
            default_reasons = {
                "ko": "평가 결과를 가져올 수 없습니다.",
                "en": "Cannot retrieve evaluation result.",
                "jp": "評価結果を取得できません。"
            }
            reason = result.get("reason", default_reasons.get(language, default_reasons["ko"]))
            
            # 점수가 0-1 범위를 벗어나면 조정
            score = max(0.0, min(1.0, score))
            
            return {
                "policy_compliance": score,
                "reason": reason
            }
            
        except Exception as e:
            error_msgs = {
                "ko": f"LLM 평가 중 오류 발생: {str(e)}",
                "en": f"Error during LLM evaluation: {str(e)}",
                "jp": f"LLM評価中にエラーが発生しました: {str(e)}"
            }
            return {
                "policy_compliance": 0.0,
                "reason": error_msgs.get(language, error_msgs["ko"])
            }
    
    def _create_evaluation_prompt(self, response: str, expected_result: Dict, language: str = "ko") -> str:
        """Generate prompt for policy compliance evaluation"""
        
        # Load refund policy file based on language
        try:
            policy_path = config.get_data_path('refund_policy.txt', language)
            with open(policy_path, 'r', encoding='utf-8') as f:
                refund_policy = f.read()
        except FileNotFoundError:
            # Fallback to Korean policy
            try:
                with open('data/ko/refund_policy.txt', 'r', encoding='utf-8') as f:
                    refund_policy = f.read()
            except FileNotFoundError:
                not_found_msgs = {
                    "ko": "환불 정책 파일을 찾을 수 없습니다.",
                    "en": "Refund policy file not found.",
                    "jp": "返品ポリシーファイルが見つかりません。"
                }
                refund_policy = not_found_msgs.get(language, not_found_msgs["ko"])
        
        prompts = {
            "ko": f"""
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
""",
            "en": f"""
Please evaluate the policy compliance of the following refund chatbot response.

**Refund Policy Standards:**
{refund_policy}

**Chatbot Response:**
{response}

**Expected Result Information:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**Evaluation Request:**
Evaluate how well the above response complies with the refund policy on a scale of 0.0 to 1.0, and provide specific reasons.

**Response Format (JSON):**
{{
    "score": 0.85,
    "reason": "Clearly mentioned the 7-day refund period and 10% fee policy, but lacks mention of customer responsibility for shipping costs. Overall, it's a response that complies well with the policy."
}}
""",
            "jp": f"""
以下の返品チャットボットの応答のポリシー遵守度を評価してください。

**返品ポリシー基準:**
{refund_policy}

**チャットボットの応答:**
{response}

**期待結果情報:**
{json.dumps(expected_result, ensure_ascii=False, indent=2)}

**評価リクエスト:**
上記の応答が返品ポリシーをどれだけよく遵守しているか0.0から1.0のスコアで評価し、具体的な理由を提示してください。

**応答形式 (JSON):**
{{
    "score": 0.85,
    "reason": "7日間の返品期間と１０％の手数料ポリシーを明確に言及していますが、送料の顧客負担についての言及が不足しています。全体的にポリシーをよく遵守した応答です。"
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