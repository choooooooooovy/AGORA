"""대화형 프롬프트 생성 유틸리티"""

from typing import List, Dict, Any
from datetime import datetime


def build_discussion_prompt(
    base_question: str,
    previous_responses: List[Dict[str, Any]],
    current_agent: str,
    round_type: str = 'general'
) -> str:
    """
    대화 히스토리를 포함한 프롬프트 생성
    
    Args:
        base_question: 기본 질문
        previous_responses: 이전 에이전트들의 응답 리스트
            [{'turn': 1, 'agent_name': 'ValueAgent', 'response': '...', ...}, ...]
        current_agent: 현재 발언할 에이전트 이름
        round_type: 라운드 타입 ('criteria', 'comparison', 'scoring')
        
    Returns:
        대화 히스토리가 포함된 완전한 프롬프트
    """
    # 첫 번째 발언자인 경우 (대화 히스토리 없음)
    if not previous_responses:
        return base_question
    
    # 대화 히스토리 포매팅
    discussion = "\n" + "=" * 80 + "\n"
    discussion += "=== 💬 지금까지의 대화 내용 ===\n"
    discussion += "=" * 80 + "\n\n"
    
    for resp in previous_responses:
        turn = resp.get('turn', 0)
        agent_name = resp.get('agent_name', 'Unknown')
        response_text = resp.get('response', '')
        agent_weight = resp.get('agent_weight', 0)
        
        discussion += f"┌─ Turn {turn}: {agent_name}"
        if agent_weight > 0:
            discussion += f" (가중치: {agent_weight * 10}%)"
        discussion += "\n"
        discussion += "├" + "─" * 78 + "\n"
        discussion += f"{response_text}\n"
        discussion += "└" + "─" * 78 + "\n\n"
    
    # 현재 에이전트를 위한 지시사항
    discussion += "=" * 80 + "\n"
    discussion += f"=== 🎯 {current_agent}의 차례 ===\n"
    discussion += "=" * 80 + "\n\n"
    
    if round_type == 'criteria':
        instruction = f"""**당신은 {current_agent}입니다.**

위 동료들의 제안을 읽었습니다. 이제 **반드시 다음 형식으로** 응답하세요:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 이전 의견에 대한 응답

(앞서 발언한 동료들의 제안 중 동의하는 부분을 **구체적으로 언급**하세요)

예: "ValueAgent께서 제안하신 '수입 잠재력'은 중요한 기준입니다. 특히..."

### 제 의견

(당신의 전문 분야 관점에서 추가 기준을 제안하거나, 동료 의견을 보완하세요)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ 중요:** 
- 독립적인 발언만 하지 마세요
- 반드시 이전 동료들의 **구체적인 제안을 언급**하며 시작하세요
- 기존 형식(기준명, 설명, 유형, 이유)은 유지하세요
"""
    
    elif round_type == 'comparison':
        instruction = f"""**당신은 {current_agent}입니다.**

위 동료들의 의견을 들었습니다. 이제 **반드시 다음 형식으로** 응답하세요:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 이전 의견에 대한 응답

(각 동료가 제시한 비교값과 근거를 언급하세요)

예: 
- "ValueAgent께서는 A가 B보다 2배 중요하다고 하셨는데, 그 근거는..."
- "FitAgent의 의견에는 동의하지만, 한 가지 보완하고 싶은 점은..."

### 제 의견

(당신의 관점에서 비교값을 제시하고, 왜 동료와 같거나 다른지 설명하세요)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ 중요:**
- 독립적인 발언 금지
- 반드시 동료들의 의견을 **명시적으로 언급**하세요
- 최종에 명확한 비교값(숫자)을 제시하세요
"""
    
    elif round_type == 'scoring':
        instruction = f"""**당신은 {current_agent}입니다.**

위 동료들의 점수를 보았습니다. 이제 **반드시 다음 형식으로** 응답하세요:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 이전 의견에 대한 응답

(동료들이 부여한 점수를 언급하세요)

예:
- "ValueAgent는 8점을 주셨는데, 그 근거는..."
- "FitAgent의 5점은 보수적이지만, ~한 점에서 타당합니다"

### 제 의견

(당신의 관점에서 점수를 제시하고, 동료와 왜 같거나 다른지 설명하세요)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ 중요:**
- 독립적인 발언 금지
- 반드시 동료들의 점수를 **명시적으로 언급**하세요
- 최종에 명확한 점수(0-9)를 제시하세요
"""
    
    else:  # general
        instruction = f"""**당신은 {current_agent}입니다.**

위 동료들의 의견을 읽었습니다. 이제 **반드시** 다음을 수행하세요:

1. **이전 의견 언급**: 동료들이 말한 내용을 구체적으로 언급하세요
2. **응답**: 동의/반대/보완 의견을 명확히 하세요  
3. **당신의 의견**: 전문 관점에서 의견을 제시하세요

**⚠️ 독립적인 발언만 하지 마세요. 반드시 동료들을 언급하세요.**
"""
    
    return base_question + discussion + instruction


def format_conversation_history(
    conversation: List[Dict[str, Any]],
    include_director: bool = True
) -> str:
    """
    대화 히스토리를 읽기 쉬운 텍스트로 포매팅
    
    Args:
        conversation: 대화 리스트
        include_director: DirectorAgent 포함 여부
        
    Returns:
        포매팅된 대화 텍스트
    """
    if not conversation:
        return "(대화 없음)"
    
    output = []
    for msg in conversation:
        agent_name = msg.get('agent_name', 'Unknown')
        
        # DirectorAgent 제외 옵션
        if not include_director and agent_name == 'DirectorAgent':
            continue
        
        turn = msg.get('turn', 0)
        response = msg.get('response', '')
        
        output.append(f"\n[Turn {turn} - {agent_name}]")
        output.append("─" * 60)
        output.append(response)
        output.append("")
    
    return "\n".join(output)


def extract_key_points(response: str, max_length: int = 200) -> str:
    """
    응답에서 핵심 내용 추출 (요약용)
    
    Args:
        response: 전체 응답 텍스트
        max_length: 최대 길이
        
    Returns:
        요약된 텍스트
    """
    # 간단한 요약: 처음 max_length 문자 + "..."
    if len(response) <= max_length:
        return response
    
    # 문장 단위로 자르기 시도
    sentences = response.split('. ')
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) < max_length:
            summary += sentence + ". "
        else:
            break
    
    return summary.strip() + "..."


def build_director_consensus_prompt(
    conversation: List[Dict[str, Any]],
    question_context: str,
    round_type: str = 'general'
) -> str:
    """
    DirectorAgent를 위한 합의 도출 프롬프트 생성
    
    Args:
        conversation: 전체 대화 리스트
        question_context: 질문 맥락 (무엇에 대한 합의인지)
        round_type: 라운드 타입
        
    Returns:
        DirectorAgent용 프롬프트
    """
    prompt = "=" * 80 + "\n"
    prompt += "=== 🎩 DirectorAgent - 최종 합의 도출 ===\n"
    prompt += "=" * 80 + "\n\n"
    
    prompt += f"**질문**: {question_context}\n\n"
    
    prompt += "**에이전트들의 논의 내용**:\n"
    prompt += "─" * 80 + "\n"
    prompt += format_conversation_history(conversation, include_director=False)
    prompt += "\n" + "─" * 80 + "\n\n"
    
    if round_type == 'criteria':
        prompt += """**당신의 역할**:

1. **제안 분석**
   - 모든 에이전트의 제안을 종합적으로 검토
   - 중복되거나 유사한 기준 확인
   - 각 제안의 타당성 평가

2. **최종 기준 선정**
   - 최대 5개의 평가 기준 선정
   - 각 기준에 대해:
     * 기준명
     * 설명
     * 유형 (benefit/cost)
     * 선정 이유

3. **응답 형식**
```
[선정 과정]
- (논의 과정 요약)

[최종 선정 기준]
1. [기준명] (유형: benefit/cost)
   - 설명: ...
   - 선정 이유: ...

2. [기준명] (유형: benefit/cost)
   ...
```
"""
    
    elif round_type == 'comparison':
        prompt += """**당신의 역할**:

1. **의견 분석**
   - 각 에이전트의 비교값과 근거 검토
   - 의견 일치/불일치 확인
   - 차이가 나는 이유 분석

2. **가중 평균 계산**
   - 각 에이전트의 가중치를 고려하여 계산
   - 계산 과정을 명시

3. **최종 합의값 도출**
   - 가중평균을 기준으로 하되
   - 논의 내용의 설득력을 고려하여 조정
   - 최종값과 근거를 명확히 제시

4. **응답 형식**
```
[의견 분석]
- ValueAgent: 비교값 X, 근거 요약
- FitAgent: 비교값 Y, 근거 요약
- MarketAgent: 비교값 Z, 근거 요약

[가중 평균 계산]
- (계산 과정)

[최종 합의]
- 최종 확정값: (숫자)
- 근거: ...
```
"""
    
    elif round_type == 'scoring':
        prompt += """**당신의 역할**:

1. **점수 분석**
   - 각 에이전트의 점수와 근거 검토
   - 점수 분포 확인

2. **가중 평균 계산**
   - 에이전트 가중치 적용

3. **최종 점수 결정**
   - 가중평균 + 논의 내용 종합
   - 0-9 사이의 점수

4. **응답 형식**
```
[점수 분석]
- (각 에이전트 점수 요약)

[최종 점수]
- 점수: X점
- 근거: ...
```
"""
    
    return prompt
