#!/usr/bin/env python3
"""
Multi-language conversation flow test
Tests sequential conversation: greeting -> order list -> refund request
"""
import weave
from simple_chatbot import SimplifiedChatbot

def test_conversation_flow(language: str, test_inputs: list, language_name: str):
    """Test a complete conversation flow for a specific language"""
    print(f"\n{'='*60}")
    print(f"🌍 {language_name} ({language.upper()}) Conversation Test")
    print(f"{'='*60}")
    
    try:
        # Initialize chatbot for the language
        chatbot = SimplifiedChatbot(language=language)
        print(f"✅ {language_name} chatbot initialized successfully")
        
        # Test each conversation step
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n--- Step {i} ---")
            print(f"User: {user_input}")
            
            try:
                # Get bot response
                response = chatbot.chat(user_input)
                print(f"Bot: {response}")
                print("✅ Response generated successfully")
                
            except Exception as e:
                print(f"❌ Error in step {i}: {str(e)}")
                return False
                
        print(f"\n🎉 {language_name} conversation flow completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize {language_name} chatbot: {str(e)}")
        return False

def main():
    """Run conversation flow tests for all languages"""
    print("🌍 Multi-language Conversation Flow Test")
    print("Testing: 1. Greeting → 2. Recent orders → 3. Refund request")
    
    # Initialize Weave
    weave.init('wandb-korea/retail-chatbot-dev')
    
    # Define test inputs for each language
    test_scenarios = {
        "ko": {
            "name": "한국어",
            "inputs": [
                "안녕하세요",
                "최근 구매목록 3개 보여주세요",
                "키엘 크림 환불해주세요"
            ]
        },
        "en": {
            "name": "English", 
            "inputs": [
                "Hello",
                "Show me my recent 3 purchase list",
                "Please refund Kiehl's cream"
            ]
        },
        "jp": {
            "name": "日本語",
            "inputs": [
                "こんにちは", 
                "最近の購入リスト3つを見せてください",
                "キールズクリームを返品してください"
            ]
        }
    }
    
    results = {}
    
    # Test each language
    for lang_code, scenario in test_scenarios.items():
        success = test_conversation_flow(
            language=lang_code,
            test_inputs=scenario["inputs"],
            language_name=scenario["name"]
        )
        results[lang_code] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print(f"{'='*60}")
    
    all_passed = True
    for lang_code, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        lang_name = test_scenarios[lang_code]["name"]
        print(f"{lang_name} ({lang_code.upper()}): {status}")
        if not success:
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED! Multi-language conversation flows working perfectly!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    print(f"{'='*60}")
    
    return all_passed

def test_specific_language_only(language: str):
    """Test only a specific language (useful for debugging)"""
    test_scenarios = {
        "ko": {
            "name": "한국어",
            "inputs": [
                "안녕하세요",
                "최근 구매목록 3개 보여주세요", 
                "키엘 크림 환불해주세요"
            ]
        },
        "en": {
            "name": "English",
            "inputs": [
                "Hello",
                "Show me my recent 3 purchase list",
                "Please refund Kiehl's cream"
            ]
        },
        "jp": {
            "name": "日本語", 
            "inputs": [
                "こんにちは",
                "最近の購入リスト3つを見せてください",
                "キールズクリームを返品してください"
            ]
        }
    }
    
    if language not in test_scenarios:
        print(f"❌ Unsupported language: {language}")
        print(f"Available languages: {', '.join(test_scenarios.keys())}")
        return False
    
    weave.init('wandb-korea/retail-chatbot-dev')
    
    scenario = test_scenarios[language]
    return test_conversation_flow(
        language=language,
        test_inputs=scenario["inputs"], 
        language_name=scenario["name"]
    )

def test_parallel_conversations():
    """Test that different language chatbots can work in parallel"""
    print(f"\n{'='*60}")
    print("🔄 Parallel Multi-language Test")
    print(f"{'='*60}")
    
    try:
        # Create chatbots for all languages
        chatbots = {
            "ko": SimplifiedChatbot(language="ko"),
            "en": SimplifiedChatbot(language="en"), 
            "jp": SimplifiedChatbot(language="jp")
        }
        print("✅ All chatbots created successfully")
        
        # Test same functionality across languages
        test_cases = [
            {
                "ko": "안녕하세요",
                "en": "Hello", 
                "jp": "こんにちは"
            },
            {
                "ko": "구매내역을 보여주세요",
                "en": "Show me purchase history",
                "jp": "購入履歴を見せてください"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Parallel Test {i} ---")
            
            for lang, user_input in test_case.items():
                try:
                    response = chatbots[lang].chat(user_input)
                    print(f"{lang.upper()}: {user_input} → Response received ({len(response)} chars)")
                except Exception as e:
                    print(f"❌ {lang.upper()} failed: {str(e)}")
                    return False
        
        print("\n🎉 Parallel conversation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Parallel test failed: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific language
        language = sys.argv[1].lower()
        if language == "parallel":
            test_parallel_conversations()
        else:
            test_specific_language_only(language)
    else:
        # Test all languages
        main()
