import json
import weave
import asyncio
from typing import Dict, List, Any
from simple_chatbot import SimplifiedChatbot
from scorers.policy_compliance_scorer import PolicyComplianceScorer
from scorers.reason_quality_scorer import ReasonQualityScorer
from scorers.refund_decision_scorer import RefundDecisionScorer
from config import config

class RefundChatbotModel(weave.Model):
    """Refund chatbot evaluation Weave Model class with multi-language support"""
    
    language: str = "ko"  # Default language
    
    @weave.op()
    def predict(self, user_query: str, order_info: Dict = None, language: str = None) -> Dict[str, Any]:
        """
        Predict chatbot response to user query
        
        Args:
            user_query: User question
            order_info: Order information (optional)
            language: Language for evaluation (ko, en, jp)
        
        Returns:
            Chatbot response and analysis results
        """
        eval_language = language or self.language
        
        try:
            # Create chatbot instance with specified language and generate response
            chatbot = SimplifiedChatbot(language=eval_language)
            response = chatbot.chat(user_query, order_info)
            
            return {
                "response": response,
                "raw_response": response,
                "language": eval_language
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "raw_response": f"Error: {str(e)}",
                "language": eval_language
            }

# Multi-language evaluation functions
@weave.op()
def policy_compliance_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """Policy compliance evaluation - LLM-based scoring with reason"""
    scorer = PolicyComplianceScorer()
    language = output.get("language", "ko")
    result = scorer.score(target, output, language)
    return {
        "accuracy": result.get("policy_compliance", 0.0),
        "reason": result.get("reason", "Evaluation failed")
    }

@weave.op()
def reasoning_performance_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """Reasoning performance evaluation - LLM-based scoring with reason"""
    scorer = ReasonQualityScorer()
    language = output.get("language", "ko")
    result = scorer.score(target, output, language)
    return {
        "accuracy": result.get("reason_score", 0.0),
        "reason": result.get("reason", "Evaluation failed")
    }

@weave.op()
def refund_accuracy_evaluation(target: Dict, output: Dict) -> Dict[str, Any]:
    """Refund accuracy evaluation - LLM-based evaluation (refund decision accuracy only)"""
    scorer = RefundDecisionScorer()
    language = output.get("language", "ko")
    result = scorer.score(target, output, language)
    return {
        "accuracy": result.get("accuracy", 0.0),  # Refund eligibility accuracy
        "reason": result.get("reason", "No evaluation result")
    }

def load_evaluation_dataset(language: str = "ko"):
    """Load evaluation dataset with language support"""
    try:
        # Load language-specific evaluation data
        data_path = config.get_data_path('evaluate_refund.json', language)
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        # Fallback to Korean data
        with open('data/ko/evaluate_refund.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # Extract test_cases array from new JSON structure
    test_cases = data.get("test_cases", [])
    
    # Convert to Weave Evaluation format
    examples = []
    for item in test_cases:
        example = {
            "id": item["test_id"],
            "user_query": item["user_query"],
            "order_info": item["order_info"],
            "scenario": item["scenario"],
            "target": item["expected_result"],
            "language": language  # Add language information
        }
        examples.append(example)
    
    return examples

async def main(language: str = "ko"):
    """Main evaluation function with language support"""
    # Initialize Weave
    weave.init('retail-chatbot-dev')
    
    # Create model with specified language
    model = RefundChatbotModel(language=language)
    
    # Load dataset for the specified language
    examples = load_evaluation_dataset(language)
    
    language_names = {"ko": "한국어", "en": "English", "jp": "日本語"}
    lang_name = language_names.get(language, language)
    
    print(f"📊 {len(examples)} test scenarios loaded for {lang_name} ({language.upper()})")
    
    # Evaluation configuration - 3 core evaluations
    evaluation = weave.Evaluation(
        name=f"refund_chatbot_{language}_evaluation",
        dataset=examples,
        scorers=[
            policy_compliance_evaluation,      # Policy compliance
            reasoning_performance_evaluation,  # Reasoning performance
            refund_accuracy_evaluation        # Refund accuracy
        ]
    )
    
    if language == "ko":
        print("🚀 환불 챗봇 평가 시작...")
        print("📋 평가 항목:")
        print("   1. 정책 준수 (Policy Compliance) - LLM 기반 평가 (점수 + 이유)")
        print("   2. 추론 성능 (Reasoning Performance) - LLM 기반 평가 (점수 + 이유)")
        print("   3. 환불 정확도 (Refund Accuracy) - LLM 기반 평가 (점수 + 이유)")
    elif language == "en":
        print("🚀 Starting refund chatbot evaluation...")
        print("📋 Evaluation items:")
        print("   1. Policy Compliance - LLM-based evaluation (score + reason)")
        print("   2. Reasoning Performance - LLM-based evaluation (score + reason)")
        print("   3. Refund Accuracy - LLM-based evaluation (score + reason)")
    elif language == "jp":
        print("🚀 返品チャットボット評価を開始...")
        print("📋 評価項目:")
        print("   1. ポリシー遵守 (Policy Compliance) - LLMベース評価 (スコア + 理由)")
        print("   2. 推論性能 (Reasoning Performance) - LLMベース評価 (スコア + 理由)")
        print("   3. 返品精度 (Refund Accuracy) - LLMベース評価 (スコア + 理由)")
    
    # Execute evaluation
    results = await evaluation.evaluate(model)
    
    if language == "ko":
        print("\n✅ 평가 완료!")
    elif language == "en":
        print("\n✅ Evaluation completed!")
    elif language == "jp":
        print("\n✅ 評価完了!")
        
    print(f"📈 Results: {results}")
    
    return results

async def evaluate_all_languages():
    """Evaluate chatbot for all supported languages"""
    print("🌍 Multi-language Chatbot Evaluation")
    print("=" * 60)
    
    languages = ["ko", "en", "jp"]
    all_results = {}
    
    for lang in languages:
        print(f"\n🔄 Evaluating {lang.upper()} chatbot...")
        try:
            result = await main(lang)
            all_results[lang] = result
            print(f"✅ {lang.upper()} evaluation completed")
        except Exception as e:
            print(f"❌ {lang.upper()} evaluation failed: {e}")
            all_results[lang] = {"error": str(e)}
    
    print("\n" + "=" * 60)
    print("📊 Multi-language Evaluation Summary")
    print("=" * 60)
    
    for lang, result in all_results.items():
        if "error" in result:
            print(f"{lang.upper()}: ❌ Failed - {result['error']}")
        else:
            print(f"{lang.upper()}: ✅ Completed")
    
    return all_results
    

# Interactive language selection
def _prompt_language_selection() -> str:
    """Prompt user to select a language (or all) interactively."""
    language_names = {"ko": "한국어", "en": "English", "jp": "日本語"}
    supported = list(config.SUPPORTED_LANGUAGES)
    options = supported + ["all"]

    print("\n🌍 다국어 평가를 위한 언어를 선택하세요:")
    for idx, code in enumerate(options, start=1):
        if code == "all":
            print(f"  {idx}. 전체 언어 평가 (ALL)")
        else:
            print(f"  {idx}. {language_names.get(code, code)} ({code.upper()})")

    print("  0. 종료 (Exit)")

    while True:
        choice = input("\n번호를 입력하세요 (기본: 1): ").strip()
        if choice == "":
            return supported[0]  # default first supported (usually 'ko')
        if choice.isdigit():
            num = int(choice)
            if num == 0:
                return ""  # signal exit
            if 1 <= num <= len(options):
                return options[num - 1]
        # Also allow direct code input like 'ko', 'en', 'jp', or 'all'
        lowered = choice.lower()
        if lowered in options:
            return lowered
        print("❗️잘못된 입력입니다. 다시 시도하세요.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "all":
            # Evaluate all languages
            asyncio.run(evaluate_all_languages())
        else:
            # Evaluate specific language
            language = sys.argv[1].lower()
            if language in config.SUPPORTED_LANGUAGES:
                asyncio.run(main(language))
            else:
                print(f"❌ Unsupported language: {language}")
                print(f"Supported languages: {', '.join(config.SUPPORTED_LANGUAGES)}")
    else:
        # Interactive language selection when no args provided
        selected = _prompt_language_selection()
        if selected == "":
            print("👋 종료합니다.")
        elif selected == "all":
            asyncio.run(evaluate_all_languages())
        else:
            asyncio.run(main(selected))