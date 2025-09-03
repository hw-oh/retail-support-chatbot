# Multi-language Support for Retail Support Chatbot

This project now supports three languages: Korean (ko), English (en), and Japanese (jp).

## Features

### Supported Languages
- **Korean (한국어)**: Default language, fully supported
- **English**: Complete translation of prompts and interface
- **Japanese (日本語)**: Complete translation of prompts and interface

### Multi-language Components

#### 1. Configuration
- Language setting in `config.py`
- Automatic data path resolution for localized files
- Language validation and fallback mechanisms

#### 2. Data Files
- `data/refund_policy.txt` (Korean - original)
- `data/en/refund_policy.txt` (English translation)
- `data/jp/refund_policy.txt` (Japanese translation)

#### 3. Prompts
- Intent classification prompts for all languages
- Agent system prompts (order, refund, general) for all languages
- Localized user prompts and instructions

#### 4. Agents
All agents now support language parameters:
- `IntentAgent(llm_client, language="ko")`
- `OrderAgent(llm_client, language="ko")`
- `RefundAgent(llm_client, language="ko")`
- `GeneralAgent(llm_client, language="ko")`
- `PlanningAgent(llm_client, language="ko")`

## Usage

### Basic Usage
```python
from simple_chatbot import SimplifiedChatbot

# Create chatbot with specific language
chatbot = SimplifiedChatbot(language="en")  # or "ko", "jp"

# Chat
response = chatbot.chat("Hello, I want to check my orders")
print(response)
```

### Language Switching
```python
chatbot = SimplifiedChatbot(language="ko")

# Change language during runtime
chatbot.set_language("en")
response = chatbot.chat("Show me my recent orders")
```

### Interactive Mode
```bash
python simple_chatbot.py
```
The chatbot will prompt for language selection at startup.

### Demo Script
```bash
python multilingual_demo.py
```
Runs demonstration conversations in all three languages.

## File Structure
```
retail-support-chatbot/
├── data/
│   ├── ko/                        # Korean data files
│   │   ├── refund_policy.txt
│   │   ├── policy_compliance.txt
│   │   ├── catalog.json
│   │   ├── purchase_history.json
│   │   ├── evaluate_refund.json
│   │   └── evaluation_refund.json
│   ├── en/                        # English data files
│   │   ├── refund_policy.txt
│   │   ├── policy_compliance.txt
│   │   ├── catalog.json
│   │   ├── purchase_history.json
│   │   └── evaluate_refund.json
│   └── jp/                        # Japanese data files
│       ├── refund_policy.txt
│       ├── policy_compliance.txt
│       ├── catalog.json
│       ├── purchase_history.json
│       └── evaluate_refund.json
├── prompts/
│   ├── intent_prompts.py          # Multi-language intent prompts
│   ├── agent_prompts.py           # Multi-language agent prompts
│   └── weave_prompts.py           # Multi-language prompt manager
├── agents/                        # All agents support language parameter
├── config.py                      # Language configuration
├── simple_chatbot.py              # Main chatbot with language support
└── multilingual_demo.py           # Multi-language demonstration
```

## Configuration

### Environment Variables
```bash
export LANGUAGE=en  # Set default language (ko, en, jp)
```

### Code Configuration
```python
from config import config

# Set language globally
config.set_language("en")

# Get localized data path
policy_path = config.get_data_path("refund_policy.txt", "en")
```

## Implementation Details

### Prompt Management
The `WeavePromptManager` class automatically handles:
- Language-specific prompt loading
- Fallback to Korean if localized version not available
- Dynamic language switching

### Agent Architecture
Each agent:
- Accepts a `language` parameter in constructor
- Uses localized prompts automatically
- Formats user prompts in the specified language
- Maintains conversation context in the appropriate language

### Data Localization
- Korean data files remain in the root `data/` directory
- Other languages are in `data/{language}/` subdirectories
- Automatic fallback to Korean data if localized version doesn't exist

## Adding New Languages

1. **Add language code to config**:
   ```python
   SUPPORTED_LANGUAGES: list = ["ko", "en", "jp", "new_lang"]
   ```

2. **Create data directory**:
   ```bash
   mkdir data/new_lang
   ```

3. **Translate data files**:
   ```bash
   cp data/refund_policy.txt data/new_lang/refund_policy.txt
   # Edit and translate the file
   ```

4. **Add prompts**:
   - Add entries to `INTENT_PROMPTS` and `AGENT_PROMPTS` dictionaries
   - Follow existing language structure

5. **Update UI strings**:
   - Add language-specific messages in chatbot interface
   - Update welcome messages and prompts

## Testing

### Conversation Flow Tests
Test complete conversation flows (greeting → order list → refund request):

```bash
# Test all languages
python test_multilingual_conversation.py

# Test specific language only
python test_multilingual_conversation.py ko   # Korean only
python test_multilingual_conversation.py en   # English only  
python test_multilingual_conversation.py jp   # Japanese only

# Test parallel conversations
python test_multilingual_conversation.py parallel
```

### Component Demos
Run the multilingual demo to test all languages:
```bash
python multilingual_demo.py           # Chatbot demo
python multilingual_scorer_demo.py    # Scorer demo
```

### Manual Testing
Test individual languages:
```python
# Test Korean
chatbot_ko = SimplifiedChatbot(language="ko")
response = chatbot_ko.chat("최근 주문을 보여주세요")

# Test English  
chatbot_en = SimplifiedChatbot(language="en")
response = chatbot_en.chat("Show me my recent orders")

# Test Japanese
chatbot_jp = SimplifiedChatbot(language="jp")
response = chatbot_jp.chat("最近の注文を見せてください")
```

### Test Conversation Scenarios
Each language test includes:
1. **Greeting**: "안녕하세요" / "Hello" / "こんにちは"
2. **Order Inquiry**: "최근 구매목록 3개 보여주세요" / "Show me my recent 3 purchase list" / "最近の購入リスト3つを見せてください"
3. **Refund Request**: "키엘 크림 환불해주세요" / "Please refund Kiehl's cream" / "キールズクリームを返品してください"

### Evaluation System Testing
Test the multilingual evaluation system:

```bash
# Evaluate specific language
python evaluate_chatbot.py ko        # Korean evaluation
python evaluate_chatbot.py en        # English evaluation  
python evaluate_chatbot.py jp        # Japanese evaluation
python evaluate_chatbot.py all       # All languages evaluation

# Evaluation demos
python multilingual_evaluation_demo.py        # Full demo
python multilingual_evaluation_demo.py quick  # Quick test
```

The evaluation system includes:
- **Policy Compliance**: LLM-based policy adherence scoring
- **Reasoning Performance**: LLM-based explanation quality scoring  
- **Refund Accuracy**: LLM-based refund decision accuracy scoring

All evaluations are performed in the target language with language-appropriate datasets and prompts.

## Notes

- All comments in the code have been updated to English
- The system maintains backward compatibility with Korean as the default language
- Language switching is supported during runtime without restarting the chatbot
- Weave prompt registration supports multiple languages with appropriate naming conventions
