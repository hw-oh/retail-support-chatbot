#!/usr/bin/env python3
"""
Multi-language scorer demonstration
"""
import json
from scorers.policy_compliance_scorer import PolicyComplianceScorer
from scorers.refund_decision_scorer import RefundDecisionScorer
from scorers.reason_quality_scorer import ReasonQualityScorer

def demo_multilingual_scorers():
    """Demonstrate multilingual scoring capabilities"""
    print("🌍 Multi-language Scorer Demo")
    print("=" * 50)
    
    # Create scorers
    policy_scorer = PolicyComplianceScorer()
    refund_scorer = RefundDecisionScorer()
    reason_scorer = ReasonQualityScorer()
    
    # Sample test data
    target = {
        "refund_possible": True,
        "reason": "Within 7 days and refundable category",
        "refund_fee": 2200
    }
    
    model_output = {
        "response": "Your refund is possible within 7 days with a 10% fee."
    }
    
    languages = ["ko", "en", "jp"]
    
    for language in languages:
        print(f"\n=== {language.upper()} Language Evaluation ===")
        
        try:
            # Policy compliance scoring
            policy_result = policy_scorer.score(target, model_output, language)
            print(f"📋 Policy Compliance ({language}): {policy_result['policy_compliance']:.2f}")
            print(f"   Reason: {policy_result['reason'][:100]}...")
            
            # Refund decision scoring
            refund_result = refund_scorer.score(target, model_output, language)
            print(f"✅ Refund Decision ({language}): {refund_result['accuracy']}")
            print(f"   Reason: {refund_result['reason'][:100]}...")
            
            # Reason quality scoring
            reason_result = reason_scorer.score(target, model_output, language)
            print(f"💭 Reason Quality ({language}): {reason_result['reason_score']:.2f}")
            print(f"   Reason: {reason_result['reason'][:100]}...")
            
        except Exception as e:
            print(f"⚠️  Error in {language}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Multilingual scorer demo completed!")
    
    # Test convenience methods
    print("\n🔧 Testing convenience methods:")
    try:
        ko_result = policy_scorer.score_ko(target, model_output)
        en_result = policy_scorer.score_en(target, model_output)
        jp_result = policy_scorer.score_jp(target, model_output)
        
        print(f"Korean method: {ko_result['policy_compliance']:.2f}")
        print(f"English method: {en_result['policy_compliance']:.2f}")
        print(f"Japanese method: {jp_result['policy_compliance']:.2f}")
        print("✅ All convenience methods working!")
        
    except Exception as e:
        print(f"⚠️  Error in convenience methods: {str(e)}")

def demo_data_loading():
    """Demonstrate multilingual data loading"""
    print("\n📁 Multi-language Data Loading Demo")
    print("=" * 50)
    
    from config import config
    
    languages = ["ko", "en", "jp"]
    
    for language in languages:
        print(f"\n=== {language.upper()} Data ===")
        
        try:
            # Test policy file loading
            policy_path = config.get_data_path('refund_policy.txt', language)
            with open(policy_path, 'r', encoding='utf-8') as f:
                policy_content = f.read()[:100]
            print(f"📄 Policy file ({language}): {policy_content}...")
            
            # Test catalog loading
            catalog_path = config.get_data_path('catalog.json', language)
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)
            print(f"🛍️  Catalog ({language}): {len(catalog_data)} products")
            print(f"   First product: {catalog_data[0]['product_name']}")
            
            # Test purchase history loading
            history_path = config.get_data_path('purchase_history.json', language)
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            print(f"📦 Purchase history ({language}): {len(history_data)} orders")
            print(f"   First order: {history_data[0]['product_name']}")
            
        except FileNotFoundError as e:
            print(f"⚠️  File not found for {language}: {e}")
        except Exception as e:
            print(f"⚠️  Error loading {language} data: {e}")

def main():
    """Run all demos"""
    print("🌍 Complete Multi-language System Demo")
    print("=" * 60)
    
    # Demo scorers
    demo_multilingual_scorers()
    
    # Demo data loading
    demo_data_loading()
    
    print("\n" + "=" * 60)
    print("🎉 Complete multi-language system is ready!")
    print("Supported components:")
    print("✅ Chatbot (Korean, English, Japanese)")
    print("✅ Agents (Intent, Order, Refund, General, Planning)")
    print("✅ Scorers (Policy Compliance, Refund Decision, Reason Quality)")
    print("✅ Data Files (Policies, Catalogs, Purchase History, Evaluation)")
    print("✅ Prompts (Intent Classification, Agent System Prompts)")

if __name__ == "__main__":
    main()
