# 쇼핑몰 챗봇 (LLM 기반)

GPT-4o를 활용한 고객 서비스 챗봇입니다.

## 주요 특징

- **순수 LLM 기반 아키텍처**: 룰베이스 없이 프롬프트 엔지니어링으로 모든 로직 처리
- **Multi-turn 대화 지원**: 매 턴마다 동적으로 액션을 결정하여 복잡한 연속 대화 처리
- **컨텍스트 기반 대화**: 이전 대화 내용과 도구 실행 결과를 기억하고 활용
- **도구 결과 캐싱**: 효율적인 도구 실행 및 결과 재사용으로 응답 속도 향상
- **대화 상태 관리**: 현재 대화 단계와 활성 컨텍스트를 추적하여 일관된 대화 제공
- **비용 최적화**: 도구 실행에 gpt-4o-mini 모델 사용으로 비용 절감

## 프로젝트 구조

```
customer-support-chatbot/
├── agents/                 # LLM 기반 에이전트들
│   ├── base.py            # OpenAI 클라이언트
│   ├── shopping_mall_agent.py    # 메인 에이전트 (Multi-turn 대화 지원)
│   ├── intent_classifier.py      # 의도 분류 에이전트
│   ├── plan_generator.py         # 계획 생성 에이전트
│   ├── response_generator.py     # 응답 생성 에이전트
│   ├── conversation_context.py   # 대화 컨텍스트 에이전트
│   └── plan_step.py             # 계획 단계 클래스
│
├── tools/                  # 도구들 (환불, 주문, 제품 조회 등)
│   ├── catalog_tool.py
│   ├── order_history_tool.py
│   ├── refund_*.py
│   └── ...
│
├── data/                   # 데이터 파일들
│   ├── catalog.json       # 제품 카탈로그
│   ├── purchase_history.json  # 구매 이력
│   ├── refund_policy.txt      # 환불 정책
│   └── evaluate_refund.json   # 평가 데이터
│
├── demo/                   # 데모 스크립트들
│   ├── demo.py            # 시나리오 데모
│   ├── demo_date_query.py # 날짜 쿼리 데모
│   └── demo_multi_turn.py # Multi-turn 대화 데모
│
├── tests/                  # 테스트 파일들
│   ├── test_tools.py      # 도구 테스트
│   ├── test_date_query.py # 날짜 쿼리 테스트
│   └── test_updated_dates.py # 날짜 업데이트 테스트
│
├── scripts/                # 유틸리티 스크립트
│   └── update_dates.py    # 날짜 업데이트 스크립트
│
├── main.py                # 메인 실행 파일 (대화형 챗봇)
├── config.py              # 설정 파일
└── requirements.txt       # 의존성 패키지

```

## 설치 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
   - `env.example` 파일을 `.env`로 복사
   - OpenAI API 키 설정
   
```bash
cp env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 설정
```

## 실행 방법

### 대화형 챗봇 실행
```bash
python main.py
```

### 데모 시나리오 실행
```bash
python demo/demo.py
```

### 테스트 실행
```bash
python tests/test_tools.py
```

## 주요 특징

- **순수 LLM 기반 아키텍처**: 모든 주요 컴포넌트가 rule-based 로직 없이 LLM으로 작동
- **LLM 기반 의도 분류**: 자연어 이해로 정확한 의도 파악 (clarification intent 지원)
- **동적 계획 수립**: 상황에 맞는 도구 선택 및 실행
- **컨텍스트 유지**: 멀티턴 대화 지원 및 이전 대화 참조
- **자연스러운 응답**: GPT-4o를 활용한 한국어 응답 생성
- **LLM 기반 환불 검증**: 제품 정보와 환불 정책을 종합적으로 고려한 판단

## 에이전트 구성

### 1. ShoppingMallAgent (메인)
- 전체 대화 흐름 제어
- 세션 관리
- 도구 실행 조정

### 2. IntentClassifierAgent (LLM 기반)
- 사용자 의도 분류 (환불, 주문조회, 제품검색, clarification 등)
- 엔티티 추출 (주문번호, 제품명, 날짜 등)
- 이전 대화 참조 감지 ("그 중에", "다른 것" 등)

### 3. PlanGeneratorAgent (LLM 기반)
- 의도에 따른 실행 계획 생성
- 도구 간 의존성 관리

### 4. ResponseGeneratorAgent (LLM 기반)
- 결과를 자연스러운 한국어로 변환
- 상황별 적절한 톤 사용
- 모든 도구 결과 통합 표시

### 5. ConversationContextAgent
- 대화 이력 추적
- 컨텍스트 정보 관리

## 주요 도구들 (LLM 기반)

### OrderHistoryTool (gpt-4o-mini)
- 주문 이력 조회
- 컨텍스트 인식 ("다른" 주문 필터링)

### RefundValidatorTool (gpt-4o-mini)
- 환불 가능 여부 검증
- 환불 정책 기반 판단

## 사용 방법

### 대화형 모드 (main.py)
```bash
$ python main.py

============================================================
🛍️  쇼핑몰 고객 서비스 챗봇에 오신 것을 환영합니다!
============================================================

💬 제품 검색, 주문 조회, 환불 문의 등을 도와드릴 수 있습니다.
📝 대화를 종료하려면 'exit', 'quit', '종료' 중 하나를 입력하세요.
🔄 새로운 대화를 시작하려면 'new', '새로고침'을 입력하세요.

✅ 챗봇이 준비되었습니다. 무엇을 도와드릴까요?
------------------------------------------------------------

👤 고객님: 
```

### 주요 명령어
- **종료**: `exit`, `quit`, `종료`
- **새 대화**: `new`, `새로고침`
- **디버그 모드**: 환경변수 `DEBUG=true` 설정

## 대화 예시

```
사용자: 최근에 산 마우스가 고장났어요
챗봇: 고객님, 마우스 고장으로 불편을 드려 죄송합니다. 
      환불이나 교환을 도와드리겠습니다. 언제 구매하셨나요?

사용자: 3일 전에 샀어요
챗봇: 마이크로소프트 마우스를 3일 전에 구매하신 것을 확인했습니다.
      환불이 가능합니다. 환불 수수료는 없으며, 
      전액 45,000원을 환불받으실 수 있습니다.
      환불을 진행하시겠습니까?

사용자: 네, 환불해주세요
챗봇: 환불이 정상적으로 처리되었습니다. 
      환불번호는 REF20250822143000001입니다.
      영업일 기준 3-5일 내에 환불금이 입금될 예정입니다.
```
