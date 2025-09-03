#!/usr/bin/env python3
"""
Weave prompt registration and management
"""
import weave
from datetime import datetime
from .intent_prompts import INTENT_PROMPTS
from .agent_prompts import AGENT_PROMPTS
from config import config


# Load refund policy based on language
def load_refund_policy(language: str = None):
    try:
        import os
        from config import config
        
        if language is None:
            language = config.LANGUAGE
            
        # All languages now have their own subdirectory
        policy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', language, 'refund_policy.txt')
            
        with open(policy_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Refund policy file not found."

def register_all_prompts(language: str = "ko"):
    """Register all prompts to Weave (using official StringPrompt class)"""
    from config import config
    
    if language not in config.SUPPORTED_LANGUAGES:
        language = "ko"
    
    print(f"🔄 Registering prompts to Weave for language: {language}...")
    
    # Register prompts using Weave StringPrompt class
    prompts_to_register = {
        f"intent_classifier_{language}": {
            "content": INTENT_PROMPTS[language]["system"],
            "description": f"{language.upper()} shopping mall customer service intent classification prompt (template variable: {{current_date}})"
        },
        f"order_agent_system_{language}": {
            "content": AGENT_PROMPTS[language]["order_agent"]["system"],
            "description": f"{language.upper()} order inquiry and management specialist agent system prompt"
        },
        f"refund_agent_system_{language}": {
            "content": AGENT_PROMPTS[language]["refund_agent"]["system"] % load_refund_policy(language),
            "description": f"{language.upper()} refund processing and policy guidance specialist agent system prompt"
        },
        f"general_agent_system_{language}": {
            "content": AGENT_PROMPTS[language]["general_agent"]["system"],
            "description": f"{language.upper()} general customer service response agent system prompt"
        }
    }
    
    registered_refs = {}
    
    for name, prompt_info in prompts_to_register.items():
        try:
            # Use official StringPrompt class
            prompt_obj = weave.StringPrompt(prompt_info["content"])
            weave.publish(prompt_obj, name=name)
            registered_refs[name] = name
            print(f"✅ {name} prompt registration completed - {prompt_info['description']}")
        except Exception as e:
            print(f"⚠️ {name} prompt registration failed: {e}")
            # Fallback to local prompts
            registered_refs[name] = name
    
    print("🎉 All prompts registration completed!")
    return {
        "intent_classifier": f"intent_classifier_{language}",
        "order_agent": f"order_agent_system_{language}", 
        "refund_agent": f"refund_agent_system_{language}",
        "general_agent": f"general_agent_system_{language}"
    }


def get_prompt_from_weave(prompt_name: str, **kwargs) -> str:
    """Get StringPrompt object from Weave and call format() (works without Weave)"""
    
    # Use local prompts directly if Weave is disabled
    import os
    if os.getenv('WEAVE_INIT_DISABLED') == '1':
        return get_fallback_prompt(prompt_name, **kwargs)
    
    try:
        # Get StringPrompt object from Weave
        ref = weave.ref(prompt_name)
        prompt_obj = ref.get()
        
        # Use StringPrompt.format() method
        if kwargs:
            return prompt_obj.format(**kwargs)
        else:
            return prompt_obj.format()
        
    except Exception as e:
        # Quietly fallback in dev/test environment
        if os.getenv('WEAVE_INIT_DISABLED') == '1':
            pass  # Quiet fallback
        else:
            print(f"⚠️ Failed to get prompt from Weave ({prompt_name}): {e}")
            print("📁 Falling back to local prompts.")
        
        # Fallback: use local prompts
        return get_fallback_prompt(prompt_name, **kwargs)


def get_fallback_prompt(prompt_name: str, **kwargs) -> str:
    """Local prompt fallback when Weave fails"""
    from config import config
    
    # Extract language from prompt name
    language = "ko"  # default
    for lang in config.SUPPORTED_LANGUAGES:
        if prompt_name.endswith(f"_{lang}"):
            language = lang
            break
    
    fallback_prompts = {
        f"intent_classifier_{language}": INTENT_PROMPTS[language]["system"],
        f"order_agent_system_{language}": AGENT_PROMPTS[language]["order_agent"]["system"],
        f"refund_agent_system_{language}": AGENT_PROMPTS[language]["refund_agent"]["system"] % load_refund_policy(language),
        f"general_agent_system_{language}": AGENT_PROMPTS[language]["general_agent"]["system"]
    }
    
    prompt = fallback_prompts.get(prompt_name, "Prompt not found.")
    
    if kwargs:
        return prompt.format(**kwargs)
    return prompt


class WeavePromptManager:
    """Prompt manager - use local prompts directly in development mode"""
    
    def __init__(self, use_local_only: bool = None):
        """
        Args:
            use_local_only: If True, always use local prompts, if None, decide by environment variable
        """
        import os
        if use_local_only is None:
            # Decide by environment variable (default: use local)
            self.use_local_only = os.getenv('USE_LOCAL_PROMPTS', '1') == '1'
        else:
            self.use_local_only = use_local_only
            
        # Set prompt references based on current language
        from config import config
        self.language = config.LANGUAGE
        self.prompt_refs = {
            "intent_classifier": f"intent_classifier_{self.language}",
            "order_agent": f"order_agent_system_{self.language}",
            "refund_agent": f"refund_agent_system_{self.language}", 
            "general_agent": f"general_agent_system_{self.language}"
        }
    
    def get_intent_prompt(self, current_date: str = None) -> str:
        """Get intent classification prompt"""
        if current_date is None:
            current_date = config.CURRENT_DATE
        
        if self.use_local_only:
            # Use local prompts directly (immediate reflection)
            prompt = INTENT_PROMPTS[self.language]["system"]
            return prompt.format(current_date=current_date)
        else:
            # Use Weave prompts
            return get_prompt_from_weave(
                self.prompt_refs["intent_classifier"],
                current_date=current_date
            )
    
    def get_order_agent_prompt(self) -> str:
        """Get order agent prompt"""
        if self.use_local_only:
            return AGENT_PROMPTS[self.language]["order_agent"]["system"]
        else:
            return get_prompt_from_weave(self.prompt_refs["order_agent"])
    
    def get_refund_agent_prompt(self) -> str:
        """Get refund agent prompt"""
        if self.use_local_only:
            return AGENT_PROMPTS[self.language]["refund_agent"]["system"] % load_refund_policy(self.language)
        else:
            return get_prompt_from_weave(self.prompt_refs["refund_agent"])
    
    def get_general_agent_prompt(self) -> str:
        """Get general agent prompt"""
        if self.use_local_only:
            return AGENT_PROMPTS[self.language]["general_agent"]["system"]
        else:
            return get_prompt_from_weave(self.prompt_refs["general_agent"])
    
    def set_language(self, language: str):
        """Set the language for prompts"""
        from config import config
        if language in config.SUPPORTED_LANGUAGES:
            self.language = language
            # Update prompt references
            self.prompt_refs = {
                "intent_classifier": f"intent_classifier_{self.language}",
                "order_agent": f"order_agent_system_{self.language}",
                "refund_agent": f"refund_agent_system_{self.language}", 
                "general_agent": f"general_agent_system_{self.language}"
            }


# Global prompt manager instance
prompt_manager = WeavePromptManager()


if __name__ == "__main__":
    # Initialize Weave
    weave.init("retail-chatbot-dev")
    
    # Register prompts
    register_all_prompts()
    
    # Test
    print("\n🔍 Prompt test:")
    manager = WeavePromptManager()
    intent_prompt = manager.get_intent_prompt()
    print(f"Intent prompt length: {len(intent_prompt)} characters")
    
    order_prompt = manager.get_order_agent_prompt()
    print(f"Order prompt length: {len(order_prompt)} characters")
