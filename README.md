## Retail Support Chatbot (Multi-language)

A multi-language (ko/en/jp) retail customer support chatbot. It runs a pipeline of intent classification → planning → domain agent execution → response generation, while maintaining multi-turn conversational context.

### Features
- **Multi-language support**: Korean (ko), English (en), Japanese (jp)
- **Multi-turn management**: Structured context passed and accumulated across agents
- **Agent architecture**: Intent, Order, Refund, General, and Planning agents
- **Multi-language evaluation**: Per-language datasets for policy compliance, reasoning quality, and refund accuracy

### Quick Start
1) Install dependencies
```bash
pip install -r requirements.txt
```

2) Set environment variables
```bash
export OPENAI_API_KEY=YOUR_KEY
# Optional: use local prompts only (default 1)
export USE_LOCAL_PROMPTS=1
```

3) Run the chatbot (interactive language selection)
```bash
python simple_chatbot.py
```

4) Run evaluation (interactive language selection supported)
```bash
python evaluate_chatbot.py          # Shows a language selection menu
python evaluate_chatbot.py ko       # Evaluate a specific language
python evaluate_chatbot.py all      # Evaluate all languages
```

### Conversation flow examples
Below are sample inputs for each language (Greeting → Recent orders → Refund request). Start with `python simple_chatbot.py`, choose a language, then enter the following messages.

- Korean (ko)
  - "안녕하세요"
  - "최근 구매목록 3개 보여주세요"
  - "키엘 크림 환불해주세요"

- English (en)
  - "Hello"
  - "Show me my recent 3 purchase list"
  - "Please refund Kiehl's cream"

- 日本語 (jp)
  - "こんにちは"
  - "最近の購入リスト3つを見せてください"
  - "キールズクリームを返品してください"

For parallel checks during development, you can query similar functions across languages concurrently; each runs with its own context.

### Project structure
```
retail-support-chatbot/
├── data/
│   ├── ko/
│   ├── en/
│   └── jp/
├── prompts/
│   ├── intent_prompts.py
│   ├── agent_prompts.py
│   └── weave_prompts.py
├── agents/
├── scorers/
├── tools/
├── simple_chatbot.py
├── evaluate_chatbot.py
└── config.py
```

### Configuration and prompts
- Manage default and supported languages via `config.py` (`LANGUAGE`, `SUPPORTED_LANGUAGES`).
- `prompts/weave_prompts.py` handles Weave-based prompt registration/loading with a local fallback.

### Evaluation system
The evaluation runs three metrics with language-specific datasets:
- Policy Compliance
- Reason Quality
- Refund Accuracy

See the “Run evaluation” section above for usage examples.

### Notes
- The default language is Korean (`ko`), and you can switch languages at runtime.
- Data and prompts follow `data/{lang}` directory layout.
- If prompt registration fails, the system automatically falls back to local prompts.

