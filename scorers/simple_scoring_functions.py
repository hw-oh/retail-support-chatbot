import weave
import json
import re
from typing import Dict, Any, Optional


# GPT-4를 사용한 LLM Judge
@weave.op()
def llm_judge_reason_quality(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """이유 설명 품질을 GPT-4로 평가"""
    
    # LLM 클라이언트 생성 (GPT-4 사용)
    from agents.base import LLMClient
    llm = LLMClient(model="gpt-4")
    
    expected_reason = expected_result.get("reason", "")
    
    # agent_data에서 실제 이유 추출
    agent_data = output.get("agent_data", {})
    if isinstance(agent_data, dict):
        actual_reason = agent_data.get("reason", "")
        user_response = agent_data.get("user_response", "")
    else:
        actual_reason = ""
        user_response = str(output.get("response", ""))
    
    if not actual_reason and not user_response:
        return {
            "reason_quality_score": 0.0,
            "evaluation": "응답이 없습니다",
            "specific_feedback": "평가할 이유나 응답이 제공되지 않았습니다"
        }
    
    judge_prompt = f"""
다음은 환불 요청에 대한 챗봇의 응답을 평가하는 작업입니다.

**기대되는 이유:** {expected_reason}

**챗봇의 실제 이유:** {actual_reason}

**챗봇의 사용자 응답:** {user_response}

다음 기준으로 챗봇의 이유 설명 품질을 평가해주세요:

1. 정확성: 기대되는 이유와 얼마나 일치하는가?
2. 완성도: 필요한 정보가 모두 포함되어 있는가?
3. 명확성: 사용자가 이해하기 쉽게 설명되어 있는가?
4. 정책 근거: 환불 정책을 올바르게 인용하고 적용했는가?

응답은 다음 JSON 형식으로 제공해주세요:
{{
    "score": 0.0-1.0 사이의 점수,
    "evaluation": "전체적인 평가 (excellent/good/fair/poor)",
    "specific_feedback": "구체적인 피드백"
}}
"""
    
    try:
        response = llm.chat([{"role": "user", "content": judge_prompt}])
        
        # JSON 파싱
        if "```json" in response:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
        
        result = json.loads(response.strip())
        
        return {
            "reason_quality_score": float(result.get("score", 0.0))
        }
        
    except Exception as e:
        return {
            "reason_quality_score": 0.0
        }


@weave.op()
def llm_judge_policy_compliance(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """정책 준수도를 GPT-4로 평가"""
    
    # LLM 클라이언트 생성 (GPT-4 사용)
    from agents.base import LLMClient
    llm = LLMClient(model="gpt-4")
    
    # 환불 정책 로드
    try:
        with open('data/refund_policy.txt', 'r', encoding='utf-8') as f:
            refund_policy = f.read()
    except:
        refund_policy = "정책 파일을 읽을 수 없습니다"
    
    # agent_data에서 정보 추출
    agent_data = output.get("agent_data", {})
    if isinstance(agent_data, dict):
        user_response = agent_data.get("user_response", "")
        policy_applied = agent_data.get("policy_applied", [])
        refund_possible = agent_data.get("refund_possible")
    else:
        user_response = str(output.get("response", ""))
        policy_applied = []
        refund_possible = None
    
    expected_refund = expected_result.get("refund_possible")
    
    judge_prompt = f"""
다음은 환불 요청에 대한 챗봇의 응답이 환불 정책을 얼마나 잘 준수하는지 평가하는 작업입니다.

**환불 정책:**
{refund_policy}

**기대되는 환불 가능 여부:** {expected_refund}
**챗봇의 환불 판단:** {refund_possible}
**적용된 정책:** {policy_applied}
**챗봇의 응답:** {user_response}

다음 기준으로 정책 준수도를 평가해주세요:

1. 정책 정확성: 환불 정책의 규칙을 올바르게 적용했는가?
2. 일관성: 판단과 설명이 정책과 일치하는가?
3. 완전성: 관련된 모든 정책 조항을 고려했는가?
4. 명시성: 어떤 정책 규칙을 적용했는지 명확히 설명했는가?

응답은 다음 JSON 형식으로 제공해주세요:
{{
    "score": 0.0-1.0 사이의 점수,
    "evaluation": "전체적인 평가 (excellent/good/fair/poor)",
    "specific_feedback": "구체적인 피드백",
    "policy_violations": ["위반된 정책 항목들"],
    "policy_strengths": ["잘 적용된 정책 항목들"]
}}
"""
    
    try:
        response = llm.chat([{"role": "user", "content": judge_prompt}])
        
        # JSON 파싱
        if "```json" in response:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
        
        result = json.loads(response.strip())
        
        return {
            "policy_compliance_score": float(result.get("score", 0.0))
        }
        
    except Exception as e:
        return {
            "policy_compliance_score": 0.0
        }


@weave.op()
def exact_match_refund_decision(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """환불 여부 정확도 - Exact Match"""
    
    try:
        expected = expected_result.get("refund_possible")
        
        # agent_data에서 실제 판단 추출
        agent_data = output.get("agent_data", {})
        if isinstance(agent_data, dict):
            predicted = agent_data.get("refund_possible")
        else:
            predicted = None
        
        # 디버깅 정보 (제거)
        # print(f"DEBUG exact_match_refund_decision - expected: {expected}, predicted: {predicted}, agent_data keys: {list(agent_data.keys()) if agent_data else 'None'}")
        
        if expected is None or predicted is None:
            return {
                "refund_decision_accuracy": 0.0
            }
        
        exact_match = expected == predicted
        accuracy = 1.0 if exact_match else 0.0
        
        return {
            "refund_decision_accuracy": accuracy
        }
    except Exception as e:
        return {
            "refund_decision_accuracy": 0.0
        }


@weave.op()
def exact_match_refund_fee(expected_result: Dict, output: Dict) -> Dict[str, Any]:
    """환불 수수료 정확도 - Exact Match"""
    
    expected_fee = expected_result.get("refund_fee", 0)
    
    # agent_data에서 실제 수수료 추출
    agent_data = output.get("agent_data", {})
    if isinstance(agent_data, dict):
        predicted_fee = agent_data.get("refund_fee", 0)
    else:
        predicted_fee = 0
    
    # 숫자 타입으로 변환
    try:
        expected_fee = float(expected_fee) if expected_fee is not None else 0.0
        predicted_fee = float(predicted_fee) if predicted_fee is not None else 0.0
    except (ValueError, TypeError):
        return {
            "refund_fee_accuracy": 0.0
        }
    
    exact_match = expected_fee == predicted_fee
    accuracy = 1.0 if exact_match else 0.0
    
    return {
        "refund_fee_accuracy": accuracy
    }
