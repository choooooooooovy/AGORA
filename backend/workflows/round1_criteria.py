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
You are '{agent['name']}'.
Perspective: {agent.get('perspective', 'Core value')}
Stance: {agent['debate_stance']}

User Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Interests:**
{user_input.get('interests', 'N/A')}

**Aptitudes:**
{user_input.get('aptitudes', 'N/A')}

**Core Values:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Now it's your turn. Propose evaluation criteria you think are important from your perspective.**

[Important Points]
1. Don't mention specific majors. Focus on the criteria itself.
2. **Clearly** show your perspective (persona).
3. Interpret the user's interests/aptitudes/values from your viewpoint.
4. Explain concretely how to measure this criterion.

Answer in this format:
---
제안 기준: [Criterion name]

중요성: [Explain in 200+ characters why this is important from your perspective]

측정 방법: [3+ ways to objectively evaluate this criterion]

---

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
**ALL your output MUST be in Korean.**
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
You are '{questioner['name']}'.
Perspective: {questioner.get('perspective', 'Core perspective')}
Stance: {questioner['debate_stance']}

'{target_agent['name']}' just proposed this:
---
{latest_proposal['content']}
---

**Ask sharp questions about this proposal from your perspective.**

[Important Points]
1. Don't mention specific majors, focus on the criteria itself.
2. Ask based on your perspective (persona).
3. Check if the measurement method is specific, valid, and feasible.

Question Writing Guide:
- Point out conflicts with your perspective
- Request alternative measurement methods or identify problems
- Suggest priorities from a different viewpoint

Write about 100-150 characters.

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
Examples: "그건 좀 이상한데?", "근데 그렇게 하면...", "○○야, 그건 어떻게..."
**ALL your output MUST be in Korean.**
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
You are '{answerer['name']}'.
Perspective: {answerer.get('perspective', 'Core perspective')}

Your friends asked these questions about your proposal:

{questions_text}

**Answer each question clearly and persuasively.**

[Important Points]
1. Don't mention specific majors, defend the criteria itself.
2. **Clearly** defend your perspective (persona).
3. Explain concretely why the measurement method is valid and feasible.

Answer Guide:
- Mention each questioner by name when answering
- Provide evidence for why your core values should be prioritized
- Present specific research results or statistical evidence
- About 200-300 characters

Answer in this format:
---
[Questioner name]야:
[Answer content]

[Questioner name]야:
[Answer content]
---

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
Examples: "그건 이렇게 보면 돼", "솔직히 말하면...", "네 말도 맞는데..."
**ALL your output MUST be in Korean.**
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
    
    system_prompt = """You are a fair and objective moderator. 
You must synthesize the discussion content from three experts and select the final evaluation criteria.
Balance the perspectives of each expert while choosing criteria that will be most helpful to the user."""
    
    user_prompt = f"""
The following is the content of a 12-turn debate about evaluation criteria for major selection:

{debate_summary}

---

**Mission: Based on the above debate content, select the final {max_criteria} evaluation criteria.**

Selection Principles:
1. Balance the core values of the three experts
2. Measurable and specific criteria
3. Criteria that provide practical help for the user's major selection
4. Independent criteria that don't overlap

Answer in the following JSON format:
```json
{{
  "selected_criteria": [
    {{
      "name": "Criterion name",
      "description": "Criterion description (200+ characters)",
      "source_agent": "Name of proposing Agent",
      "reasoning": "Reason for selecting this criterion"
    }}
  ],
  "summary": "Comprehensive explanation of final decision (300+ characters)"
}}
```

**Important: Answer ONLY in exact JSON format. Do not include any other text.**
**ALL field values (name, description, reasoning, summary) MUST be in Korean.**
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
