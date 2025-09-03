#!/usr/bin/env python3
"""
Multi-language chatbot demonstration
"""
import weave
from simple_chatbot import SimplifiedChatbot
from config import config

def demo_korean():
    """Korean language demo"""
    print("\n=== 한국어 데모 ===")
    chatbot = SimplifiedChatbot(language="ko")
    
    # Sample conversation
    test_inputs = [
        "안녕하세요",
        "최근 주문 3개를 보여주세요",
        "그 중에 환불 가능한 것을 알려주세요"
    ]
    
    for user_input in test_inputs:
        print(f"고객님: {user_input}")
        response = chatbot.chat(user_input)
        print(f"봇: {response}\n")

def demo_english():
    """English language demo"""
    print("\n=== English Demo ===")
    chatbot = SimplifiedChatbot(language="en")
    
    # Sample conversation
    test_inputs = [
        "Hello",
        "Show me my recent 3 orders",
        "Among them, tell me which ones are refundable"
    ]
    
    for user_input in test_inputs:
        print(f"Customer: {user_input}")
        response = chatbot.chat(user_input)
        print(f"Bot: {response}\n")

def demo_japanese():
    """Japanese language demo"""
    print("\n=== 日本語デモ ===")
    chatbot = SimplifiedChatbot(language="jp")
    
    # Sample conversation
    test_inputs = [
        "こんにちは",
        "最近の注文3つを見せてください",
        "その中で返品可能なものを教えてください"
    ]
    
    for user_input in test_inputs:
        print(f"お客様: {user_input}")
        response = chatbot.chat(user_input)
        print(f"ボット: {response}\n")

def main():
    """Run all language demos"""
    # Initialize Weave
    weave.init('wandb-korea/retail-chatbot-multilingual-demo')
    
    print("🌍 Multi-language Shopping Mall Chatbot Demo")
    print("=" * 50)
    
    # Run demos for all languages
    demo_korean()
    demo_english() 
    demo_japanese()
    
    print("=" * 50)
    print("Demo completed! All languages are now supported.")

if __name__ == "__main__":
    main()
