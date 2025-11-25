"""Round 1: 평가 기준 토론 (13-turn Debate System)"""

from typing import Dict, Any, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


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
        
        # Director 도입 발언 (Phase 시작)
        intro_turn = _director_phase_intro(state, lead_agent, phase_idx, debate_turns)
        debate_turns.append(intro_turn)
        
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
        
        # Director 정리 발언 (Phase 종료, 마지막 Phase 제외)
        if phase_idx < 3:
            summary_turn = _director_phase_summary(state, lead_agent, personas[phase_idx], phase_idx, debate_turns)
            debate_turns.append(summary_turn)
    
    # Director 의견 취합 멘트 (최종 결정 전)
    transition_turn = _director_pre_decision_transition(state, personas, debate_turns)
    debate_turns.append(transition_turn)
    
    # Phase 4: Director final decision
    director_turn = _director_final_decision(state, personas, debate_turns)
    debate_turns.append(director_turn)
    
    # State 업데이트
    state['round1_debate_turns'] = debate_turns
    state['selected_criteria'] = director_turn.get('selected_criteria', [])
    state['round1_director_decision'] = director_turn
    
    return state


# Helper functions

def _director_phase_intro(
    state: Dict[str, Any],
    lead_agent: Dict[str, Any],
    phase: int,
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Director가 각 Phase 시작 시 도입 발언"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    phase_names = ["첫 번째", "두 번째", "세 번째"]
    
    system_prompt = """You are a friendly and engaging debate moderator.
Your role is to smoothly introduce each agent's turn and keep the conversation flowing naturally."""
    
    user_prompt = f"""
This is the {phase_names[phase-1]} agent's turn to lead the discussion about evaluation criteria for major selection.

Agent to introduce: {lead_agent['name']}
Perspective: {lead_agent.get('perspective', 'Core perspective')}

**Write a brief, friendly introduction that:**
1. If first turn: Naturally start the criteria discussion
2. If not first turn: Acknowledge previous discussion briefly
3. Introduce {lead_agent['name']} WITHOUT repeating their perspective keywords
4. Ask them to propose evaluation criteria (NOT "solve problems" or similar)

**Tone:** Casual and friendly moderator
**Length:** 60-100 characters

**GOOD Examples:**
- "자, 이제 평가 기준을 정해볼까? {lead_agent['name']}에게 먼저 의견을 물어볼게."
- "좋아. 다음은 {lead_agent['name']} 차례야. 어떤 기준으로 학과를 평가하면 좋을지 말해줘."
- "{lead_agent['name']}, 이제 네 차례야. 네 관점에서 어떤 평가 기준이 필요할 것 같아?"

**BAD Examples (DON'T use):**
- "논리적 사고로 문제를 풀어볼까?" (X - 토론 목적과 맞지 않음)
- "미적 감각에 대해 이야기해줘" (X - perspective 키워드 그대로 반복)
- "{lead_agent['name']}야, ~" (X - 호칭이 부자연스러움)

**ALL your output MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": len(debate_history) + 1,
        "phase": f"Phase {phase}: {lead_agent['name']} 주도권",
        "speaker": "Director",
        "type": "phase_intro",
        "target": lead_agent['name'],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _director_phase_summary(
    state: Dict[str, Any],
    finished_agent: Dict[str, Any],
    next_agent: Dict[str, Any],
    phase: int,
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Director가 각 Phase 종료 시 정리 및 다음 Agent 소개"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # 현재 Phase의 주요 내용 추출
    current_phase_turns = [t for t in debate_history if f"Phase {phase}" in t.get('phase', '')]
    phase_summary = "\n".join([f"[{t['speaker']}]: {t['content'][:100]}..." for t in current_phase_turns[-4:]])
    
    system_prompt = """You are a friendly debate moderator.
Your role is to summarize what was discussed with rich context and insight."""
    
    user_prompt = f"""
{finished_agent['name']} just finished presenting their perspective on evaluation criteria.

Recent discussion:
{phase_summary}

Next agent: {next_agent['name']}

**Write a rich summary (2-3 sentences) that:**
1. Summarizes the SPECIFIC criteria {finished_agent['name']} proposed (use concrete criterion names)
2. Explain the REASONING/LOGIC behind the proposals - WHY these criteria matter
3. Connect to USER's characteristics mentioned in the discussion
4. Highlight what makes {finished_agent['name']}'s perspective unique
5. Do NOT introduce or mention {next_agent['name']} - they will be introduced separately

**Tone:** Casual moderator providing insightful commentary
**Length:** 150-250 characters

**GOOD Example:**
"{finished_agent['name']}는 '데이터 분석 역량'과 '문제 해결 방법론'을 제안했어. 
사용자가 논리적 사고를 강조한 점에 주목해서, 각 학과의 데이터 중심 커리큘럼과 
실전 문제 해결 교육을 평가 기준으로 삼자고 했네. 
특히 이론뿐 아니라 실무 적용 능력을 중시하는 관점이 돋보였어."

**BAD Examples:**
- "{finished_agent['name']}는 중요한 기준을 제안했어." (X - 너무 추상적)
- "{finished_agent['name']}가 두 가지 기준을 말했네." (X - 구체적 내용 없음)
- "{finished_agent['name']}의 의견이 좋았어. 이제 {next_agent['name']}야~" (X - 다음 agent 언급 금지)

**ALL your output MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": len(debate_history) + 1,
        "phase": f"Phase {phase}: {finished_agent['name']} 주도권",
        "speaker": "Director",
        "type": "phase_summary",
        "target": next_agent['name'],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _director_pre_decision_transition(
    state: Dict[str, Any],
    personas: List[Dict[str, Any]],
    debate_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Director가 최종 결정 전 의견 취합을 알리는 멘트"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    agent_names = [p['name'] for p in personas]
    
    system_prompt = """You are a professional debate moderator wrapping up the discussion."""
    
    user_prompt = f"""
All three agents ({', '.join(agent_names)}) have finished presenting their perspectives on evaluation criteria.

**Write a brief transition statement that:**
1. Acknowledges that you've heard all agents' opinions
2. Announce that you will now synthesize their input to make a final decision
3. Keep it concise and professional

**Tone:** Moderator wrapping up discussion
**Length:** 50-80 characters

**GOOD Examples:**
- "모든 에이전트들의 의견을 잘 들었어. 이제 의견을 취합해서 최종 기준을 정하겠어."
- "좋아, 세 명의 관점을 모두 들었네. 이제 종합해서 결정을 내려볼게."
- "다들 좋은 의견 고마워. 지금부터 최종 평가 기준을 선정하겠어."

**ALL your output MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": len(debate_history) + 1,
        "phase": "Phase 3 종료",
        "speaker": "Director",
        "type": "phase_summary",
        "target": None,
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


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

**Now it's your turn. Propose 2 evaluation criteria that reflect your unique perspective.**

[Critical Requirements]
1. Propose exactly **2 criteria** from your perspective
2. Both criteria must align with YOUR persona/identity, but approach from different angles
3. Don't mention specific majors - focus on criteria themselves
4. Each criterion needs: name, reasoning (WHY this criterion matters deeply)
5. Focus on WHY the criterion is important - explain the underlying logic, values, and connections to user traits
6. Don't explain HOW to measure - focus on WHY it matters

**Output Format (JSON):**
{{
  "criteria": [
    {{
      "name": "[Criterion name in Korean]",
      "reasoning": "[WHY this criterion matters from YOUR perspective. Connect to user's traits, explain the underlying logic and value. Be specific and deep. 200-300 chars]"
    }},
    {{
      "name": "[Second criterion name in Korean]",
      "reasoning": "[WHY this criterion matters from YOUR perspective. Deep explanation with clear logic. 200-300 chars]"
    }}
  ]
}}

**Example (for a logic/data-focused agent):**
{{
  "criteria": [
    {{
      "name": "데이터 분석 역량",
      "reasoning": "사용자가 논리적 사고와 문제 해결을 강조했잖아. 현대 사회에서 데이터는 객관적 의사결정의 핵심이야. 단순히 숫자를 다루는 게 아니라, 데이터 속에서 패턴과 인사이트를 찾아내고 이를 실질적 해결책으로 연결하는 능력이 필요해. 각 학과가 이런 역량을 얼마나 체계적으로 키워주는지가 중요한 거지."
    }},
    {{
      "name": "문제 해결 방법론",
      "reasoning": "논리적 사고력이 뛰어난 사용자에게는 체계적인 문제 해결 프레임워크가 중요해. 단순 암기가 아니라 복잡한 문제를 분석하고, 여러 해결 방안을 비교하며, 최적의 솔루션을 도출하는 과정을 배워야 해. 이런 방법론을 학습하면 어떤 분야에서든 적용 가능한 핵심 역량이 되거든."
    }}
  ]
}}

**Output only valid JSON, no extra text or markdown.**
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

**Critique Strategy - Use diverse patterns with evidence:**
Pattern 1 - Point out weakness with data: "{target_agent['name']}야, 그 기준은 [구체적 약점]이 있어. 실제로 [데이터/사례]를 보면..."
Pattern 2 - Suggest alternative with reasoning: "그것보다 [대안]이 더 중요해. 왜냐하면 사용자가 '[키워드]'를 강조했잖아."
Pattern 3 - Challenge with counter-evidence: "근데 [연구/통계]에 따르면 [반대 사실]인데, 어떻게 생각해?"
Pattern 4 - Raise limitation: "만약 [상황]이면 그 기준으로는 [한계]가 드러나지 않을까?"
Pattern 5 - Deepen the reasoning: "그 기준이 중요한 이유는 알겠는데, [더 깊은 질문]은 어떻게 볼 거야?"

**CRITICAL Requirements:**
- Include specific evidence, data, or user keywords in EVERY question
- Provide reasoning for your challenge
- Make it substantial, not just a simple doubt

**Length:** 100-150 characters (longer than before for better quality)

**DON'T:** "근데 창의적 표현은 왜 고려 안 해?" (too short, no evidence)
**DO:** "근데 창의적 표현도 중요하지 않아? 사용자가 '디자인'을 여러 번 언급했는데, 그 부분을 어떻게 평가할 건지 궁금해."

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
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

**Answer Strategy - Diverse response patterns:**
Pattern 1 - Acknowledge + Counterargument: "○○야, 네 말도 일리 있어. 근데 [반박]..."
Pattern 2 - Provide Evidence: "사실 [연구/통계/사례]를 보면..."
Pattern 3 - Show Bigger Picture: "그건 단기적으로는 맞는데, 장기적으로 보면..."
Pattern 4 - Turn Question Around: "오히려 그래서 내 기준이 더 중요한 거야. 왜냐하면..."
Pattern 5 - Partial Agreement + Emphasis: "맞아, [일부 동의]. 그렇지만 핵심은 [강조]..."

**Answer each questioner separately**, mentioning their name.
**Provide concrete evidence**: research findings, statistics, real-world cases, logical reasoning.
**Length:** About 150-200 characters per person (total 300-400 characters)

**Answer in this format:**
---
[Questioner name]야:
[Answer content with evidence]

[Questioner name]야:
[Answer content with evidence]
---

**DON'T** start every answer with "너 말도 맞는데..."
**DO** vary your response style while staying in character
**DON'T** use mechanical formats
**DO** write as natural conversation

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
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
    debate_history: List[Dict[str, Any]],
    add_transition: bool = True
) -> Dict[str, Any]:
    """Director가 토론 내용을 바탕으로 최종 기준 선정"""
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.0,
        max_tokens=2000  # 기준 선정 JSON이 잘리지 않도록
    )
    
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

**Mission: Based on the above debate content, select 4 evaluation criteria from the 6 proposed (3 agents × 2 criteria each).**

Selection Principles:
1. Balance the core values of the three experts (try to include criteria from all agents)
2. Measurable and specific criteria
3. Criteria that provide practical help for the user's major selection
4. **Strictly independent** criteria that don't overlap or duplicate
5. **Remove any criteria that are too similar** (keep only the stronger one)
6. Prioritize criteria with **strong evidence or concrete examples** in the debate

**Quality Check:**
- Are all 4 criteria truly different from each other?
- Can each criterion be measured objectively?
- Does each criterion reflect the user's characteristics?
- Did you consider all 6 proposed criteria fairly?

Answer in the following JSON format:
```json
{{
  "selected_criteria": [
    {{
      "name": "Criterion name",
      "description": "Criterion description (200+ characters)",
      "source_agent": "Name of proposing Agent",
      "reasoning": "Why this criterion was selected (100-150 characters)"
    }}
  ],
  "rejected_criteria": [
    {{
      "name": "Criterion name",
      "source_agent": "Name of proposing Agent",  
      "reasoning": "Why this criterion was NOT selected (100-150 characters)"
    }}
  ],
  "summary": "Overall decision explanation - connect selected criteria to user traits, explain balance between agents' perspectives (300-500 characters)"
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
    
    # JSON 파싱 시도
    decision_data = {}
    try:
        # trailing comma 제거
        cleaned_content = content.strip()
        cleaned_content = re.sub(r',\s*}', '}', cleaned_content)
        cleaned_content = re.sub(r',\s*]', ']', cleaned_content)
        
        decision_data = json.loads(cleaned_content)
        print(f"[SUCCESS] Round 1 Director final decision JSON 파싱 성공")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Round 1 JSON 파싱 실패: {e}")
        print(f"[ERROR] 실패한 내용 (첫 500자): {content[:500]}")
        
        # JSON 추출 재시도
        json_match = re.search(r'\{[^{}]*"selected_criteria"[^{}]*:.*?\]\s*[,}]', content, re.DOTALL)
        if json_match:
            try:
                decision_data = json.loads(json_match.group(0))
                print(f"[SUCCESS] 정규식으로 JSON 추출 성공")
            except:
                print(f"[ERROR] 정규식 추출도 실패")
                decision_data = {}
        else:
            decision_data = {}
    
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
