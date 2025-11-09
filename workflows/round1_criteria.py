"""Round 1: 평가 기준 토론 (13-turn Debate System)"""

import yaml
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_round1_debate(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Round 1 토론 시스템 메인 함수 (13턴 구조)
    
    Phase 1-3: 각 Agent 주도권 (4턴씩)
      - Turn 1: Agent A proposal
      - Turn 2: Agent B question to A
      - Turn 3: Agent C question to A  
      - Turn 4: Agent A answer to B&C
      ... (Agent B, C도 동일)
    
    Phase 4: Director 최종 결정 (1턴)
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state with round1_debate_turns
    """
    # 페르소나 확인
    personas = state.get('agent_personas', [])
    if not personas or len(personas) != 3:
        raise ValueError("agent_personas must have exactly 3 personas")
    
    # 초기화
    debate_turns = []
    
    # Phase 1-3: 각 Agent 주도권
    for phase_idx, lead_agent in enumerate(personas, 1):
        other_agents = [p for p in personas if p['name'] != lead_agent['name']]
        
        # Turn 1: Lead agent proposal
        proposal_turn = _agent_propose(state, lead_agent, len(debate_turns) + 1, phase_idx)
        debate_turns.append(proposal_turn)
        
        # Turn 2-3: Other agents ask questions
        for questioner in other_agents:
            question_turn = _agent_question(
                state, questioner, lead_agent, 
                len(debate_turns) + 1, phase_idx, debate_turns
            )
            debate_turns.append(question_turn)
        
        # Turn 4: Lead agent answers
        answer_turn = _agent_answer(
            state, lead_agent, other_agents,
            len(debate_turns) + 1, phase_idx, debate_turns
        )
        debate_turns.append(answer_turn)
    
    # Phase 4: Director final decision
    director_turn = _director_final_decision(state, personas, debate_turns)
    debate_turns.append(director_turn)
    
    # State 업데이트
    state['round1_debate_turns'] = debate_turns
    state['selected_criteria'] = director_turn.get('selected_criteria', [])
    state['round1_director_decision'] = director_turn
    
    return state


# Helper functions will be added next


def _agent_propose(
    state: Dict[str, Any],
    agent: Dict[str, Any],
    turn: int,
    phase: int
) -> Dict[str, Any]:
    """Agent가 평가 기준 제안"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    user_input = state['user_input']
    majors = user_input['candidate_majors']  # alternatives 대신 직접 사용
    system_prompt = agent['system_prompt']
    
    user_prompt = f"""
당신은 '{agent['name']}'입니다.
관점: {agent.get('perspective', '핵심 가치')}
입장: {agent['debate_stance']}

사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미:**
{user_input.get('interests', 'N/A')}

**적성:**
{user_input.get('aptitudes', 'N/A')}

**추구 가치:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**당신의 차례입니다. 당신의 관점에 기반한 평가 기준을 제안하세요.**

[중요 지침]
1. 특정 학과를 언급하지 마세요. 기준 자체에 집중하세요.
2. 당신의 관점(페르소나)을 **확고하게** 옹호하세요.
3. 사용자의 흥미/적성/가치관을 당신의 관점에서 해석하세요.
4. 기준의 정의와 측정 방법을 구체적으로 제시하세요.

다음 형식으로 답변하세요:
---
제안 기준: [기준 이름]

중요성: [당신의 페르소나 관점에서 왜 이 기준이 중요한지 200자 이상 설명]

측정 방법: [이 기준을 객관적으로 평가할 수 있는 구체적 방법 3가지 이상]

---
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {agent['name']} 주도권",
        "speaker": agent['name'],
        "type": "proposal",
        "target": None,
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _agent_question(
    state: Dict[str, Any],
    questioner: Dict[str, Any],
    target_agent: Dict[str, Any],
    turn: int,
    phase: int,
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Agent가 다른 Agent에게 질문"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # 가장 최근 proposal 찾기
    latest_proposal = None
    for turn_data in reversed(debate_history):
        if turn_data['type'] == 'proposal' and turn_data['speaker'] == target_agent['name']:
            latest_proposal = turn_data
            break
    
    if not latest_proposal:
        raise ValueError(f"No proposal found from {target_agent['name']}")
    
    system_prompt = questioner['system_prompt']
    user_prompt = f"""
당신은 '{questioner['name']}'입니다.
관점: {questioner.get('perspective', '핵심 관점')}
입장: {questioner['debate_stance']}

방금 '{target_agent['name']}'가 다음과 같이 제안했습니다:
---
{latest_proposal['content']}
---

**당신의 관점에서 이 제안에 대해 날카로운 질문을 하세요.**

[중요 지침]
1. 특정 학과를 언급하지 마세요. 기준 자체에 대해 질문하세요.
2. 당신의 관점(페르소나)을 바탕으로 질문하세요.
3. 측정 방법의 구체성, 타당성, 실현 가능성을 문제 삼으세요.

질문 작성 가이드:
- 당신의 관점과 충돌하는 부분을 지적
- 측정 방법의 문제점이나 대안 요구
- 다른 관점에서의 우선순위 제시

100-150자 분량으로 작성하세요.
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {target_agent['name']} 주도권",
        "speaker": questioner['name'],
        "type": "question",
        "target": target_agent['name'],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _agent_answer(
    state: Dict[str, Any],
    answerer: Dict[str, Any],
    questioners: List[Dict[str, Any]],
    turn: int,
    phase: int,
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Agent가 받은 질문들에 답변"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # 이번 phase에서 받은 질문들 찾기
    questions_received = []
    for turn_data in debate_history:
        if (turn_data['type'] == 'question' and 
            turn_data['target'] == answerer['name'] and
            f"Phase {phase}" in turn_data['phase']):
            questions_received.append(turn_data)
    
    if not questions_received:
        raise ValueError(f"No questions found for {answerer['name']} in Phase {phase}")
    
    system_prompt = answerer['system_prompt']
    questions_text = "\n\n".join([
        f"[{q['speaker']}의 질문]\n{q['content']}" 
        for q in questions_received
    ])
    
    user_prompt = f"""
당신은 '{answerer['name']}'입니다.
관점: {answerer.get('perspective', '핵심 관점')}

동료들이 당신의 제안에 대해 다음과 같은 질문을 했습니다:

{questions_text}

**각 질문에 대해 명확하고 설득력 있게 답변하세요.**

[중요 지침]
1. 특정 학과를 언급하지 마세요. 기준 자체를 방어하세요.
2. 당신의 관점(페르소나)을 **확고하게** 옹호하세요.
3. 측정 방법의 타당성과 실현 가능성을 구체적으로 설명하세요.

답변 가이드:
- 각 질문자를 언급하며 답변
- 당신의 핵심 가치가 왜 우선되어야 하는지 근거 제시
- 구체적인 연구 결과나 통계적 근거 제시
- 200-300자 분량

다음 형식으로 답변하세요:
---
[질문자 이름]님께:
[답변 내용]

[질문자 이름]님께:
[답변 내용]
---
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {answerer['name']} 주도권",
        "speaker": answerer['name'],
        "type": "answer",
        "target": [q['name'] for q in questioners],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _director_final_decision(
    state: Dict[str, Any],
    personas: List[Dict[str, Any]],
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Director가 토론 내용을 바탕으로 최종 기준 선정"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    
    # 토론 전체 내용 정리
    debate_summary = "\n\n".join([
        f"[Turn {t['turn']} - {t['speaker']} ({t['type']})]" + 
        (f" → {t['target']}" if t.get('target') else "") +
        f"\n{t['content']}"
        for t in debate_history
    ])
    
    max_criteria = state.get('max_criteria', 5)
    
    system_prompt = """당신은 공정하고 객관적인 중재자입니다. 
세 명의 전문가가 토론한 내용을 종합하여 최종 평가 기준을 선정해야 합니다.
각 전문가의 관점을 균형있게 반영하되, 사용자에게 가장 도움이 되는 기준을 선택하세요."""
    
    user_prompt = f"""
다음은 전공 선택을 위한 평가 기준에 대한 12턴의 토론 내용입니다:

{debate_summary}

---

**임무: 위 토론 내용을 바탕으로 최종 {max_criteria}개의 평가 기준을 선정하세요.**

선정 원칙:
1. 세 전문가의 핵심 가치를 골고루 반영
2. 측정 가능하고 구체적인 기준
3. 사용자의 전공 선택에 실질적 도움이 되는 기준
4. 중복되지 않는 독립적인 기준

다음 JSON 형식으로 답변하세요:
```json
{{
  "selected_criteria": [
    {{
      "name": "기준 이름",
      "description": "기준 설명 (200자 이상)",
      "source_agent": "제안한 Agent 이름",
      "reasoning": "이 기준을 선정한 이유"
    }}
  ],
  "summary": "최종 결정에 대한 종합 설명 (300자 이상)"
}}
```

**중요: 반드시 정확한 JSON 형식으로만 답변하세요. 다른 텍스트는 포함하지 마세요.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content
    
    # JSON 파싱
    import json
    import re
    
    # ```json 블록 제거
    if '```json' in content:
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
    elif '```' in content:
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
    
    try:
        decision_data = json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"응답 내용:\n{content}")
        raise
    
    return {
        "turn": len(debate_history) + 1,
        "phase": "Phase 4: Director 최종 결정",
        "speaker": "Director",
        "type": "final_decision",
        "target": None,
        "content": content,
        "selected_criteria": decision_data.get('selected_criteria', []),
        "summary": decision_data.get('summary', ''),
        "timestamp": datetime.now().isoformat()
    }
    user_input = state['user_input']
    majors = user_input['candidate_majors']  # alternatives 대신 직접 사용
    system_prompt = agent['system_prompt']
    
    user_prompt = f"""
당신은 '{agent['name']}'입니다.
관점: {agent.get('perspective', '핵심 관점')}
입장: {agent['debate_stance']}

사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미:**
{user_input.get('interests', 'N/A')}

**적성:**
{user_input.get('aptitudes', 'N/A')}

**추구 가치:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

고려 대상 전공: {', '.join(majors)}

**당신의 차례입니다. 당신의 관점에 기반한 평가 기준을 제안하세요.**

다음 형식으로 답변하세요:
---
제안 기준: [기준 이름]

설명: [왜 이 기준이 중요한지 200자 이상 설명]

측정 방법: [이 기준을 어떻게 평가할 것인지]

---
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {agent['name']} 주도권",
        "speaker": agent['name'],
        "type": "proposal",
        "target": None,
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }
