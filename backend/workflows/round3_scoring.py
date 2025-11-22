"""Round 3: 전공별 점수 평가 (13-turn Debate System)"""

import yaml
import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config import Config


# Decision Matrix score scale guide
SCORING_GUIDE = """
**Score Scale (1-9, 0.5 increments) - How suitable is each major for each criterion:**

[1.0 - 3.0] Unsuitable range
- 1.0: Very unsuitable - This major doesn't match this criterion at all
- 1.5: Almost unsuitable - Doesn't match in almost all aspects
- 2.0: Unsuitable - Doesn't match in multiple aspects
- 2.5: Somewhat unsuitable - Doesn't match in some aspects
- 3.0: Rather unsuitable - Noticeable deficiencies

[3.5 - 5.5] Average range
- 3.5: Below average - Slightly below expectations
- 4.0: Average - Decent level
- 4.5: Above average - Slightly exceeds expectations
- 5.0: Suitable - Sufficiently satisfies the criterion
- 5.5: Quite suitable - Satisfies the criterion well

[6.0 - 9.0] Suitable range
- 6.0: Very suitable - Matches the criterion very well
- 6.5: Highly suitable - Greatly exceeds the criterion
- 7.0: Excellently suitable - Very good choice
- 7.5: Very excellently suitable - Nearly ideal
- 8.0: Nearly ideal - Close to perfect
- 8.5: Almost perfect - Flawless
- 9.0: Perfectly suitable - Nothing more to wish for

**Score Selection Criteria:**
- How well does the user's MBTI traits match the major's characteristics?
- What's the likelihood the user's strengths will be utilized in this major?
- What's the likelihood the user's important values will be realized in this major?
- What about objective data (employment rate, salary, work-life balance, etc.)?

**Score Distribution Guide:**
- 8-9 points: Only for truly exceptional and perfect cases (very rare)
- 1-2 points: Only for clearly unsuitable cases (very rare)
"""


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_round3_debate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Round 3 토론 시스템 메인 함수 (13턴 구조)"""
    # 페르소나 확인
    personas = state.get('agent_personas', [])
    if not personas or len(personas) != 3:
        raise ValueError("agent_personas must have exactly 3 personas")
    
    # Round 1에서 선정된 기준 확인
    selected_criteria = state.get('selected_criteria', [])
    if not selected_criteria:
        raise ValueError("No criteria selected from Round 1")
    
    # 기준 이름 추출
    if isinstance(selected_criteria[0], dict):
        criteria_names = [c['name'] for c in selected_criteria]
    else:
        criteria_names = selected_criteria
    
    # 전공 목록 (user_input에서 직접 가져오기)
    alternatives = state.get('user_input', {}).get('candidate_majors', [])
    if not alternatives:
        raise ValueError("No alternatives provided")
    
    print(f"\n[Round 3] {len(alternatives)}개 전공 × {len(criteria_names)}개 기준 = {len(alternatives) * len(criteria_names)}개 평가")
    print(f"전공: {', '.join(alternatives)}")
    print(f"기준: {', '.join(criteria_names)}")
    
    # 초기화
    debate_turns = []
    
    # Phase 1-3: 각 Agent 주도권
    for phase_idx, lead_agent in enumerate(personas, 1):
        other_agents = [p for p in personas if p['name'] != lead_agent['name']]
        
        # Director 도입 발언 (Phase 시작)
        intro_turn = _director_phase_intro(state, lead_agent, phase_idx, debate_turns)
        debate_turns.append(intro_turn)
        
        # Turn 1: Lead agent 전체 Decision Matrix 제안
        proposal_turn = _agent_propose_matrix(
            state, lead_agent, criteria_names, alternatives,
            len(debate_turns) + 1, phase_idx
        )
        debate_turns.append(proposal_turn)
        
        # Turn 2-3: Other agents 반박
        for critic in other_agents:
            critique_turn = _agent_critique(
                state, critic, lead_agent, proposal_turn,
                len(debate_turns) + 1, phase_idx, debate_turns
            )
            debate_turns.append(critique_turn)
        
        # Turn 4: Lead agent 재반박
        defense_turn = _agent_defend(
            state, lead_agent, other_agents,
            len(debate_turns) + 1, phase_idx, debate_turns
        )
        debate_turns.append(defense_turn)
        
        # Director 정리 발언 (Phase 종료, 마지막 Phase 제외)
        if phase_idx < 3:
            summary_turn = _director_phase_summary(state, lead_agent, personas[phase_idx], phase_idx, debate_turns)
            debate_turns.append(summary_turn)
    
    # Director 의견 취합 멘트 (최종 결정 전)
    transition_turn = _director_pre_decision_transition(state, personas, debate_turns)
    debate_turns.append(transition_turn)
    
    # Phase 4: Director 최종 결정
    director_turn = _director_final_decision(
        state, personas, criteria_names, alternatives, debate_turns
    )
    debate_turns.append(director_turn)
    
    # State 업데이트
    state['round3_debate_turns'] = debate_turns
    state['decision_matrix'] = director_turn.get('decision_matrix', {})
    state['round3_director_decision'] = director_turn
    
    return state


# Helper functions

def _director_phase_intro(state, lead_agent, phase, debate_history):
    """Director가 각 Phase 시작 시 도입 발언"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    phase_names = ["첫 번째", "두 번째", "세 번째"]
    
    system_prompt = """You are a friendly debate moderator for major scoring discussion."""
    
    user_prompt = f"""
This is the {phase_names[phase-1]} agent's turn for scoring majors on evaluation criteria.

Agent: {lead_agent['name']}

**Write a brief introduction (60-100 characters) that:**
1. Introduces {lead_agent['name']} WITHOUT repeating their perspective
2. Asks them to score majors based on criteria
3. Keep it task-focused (scoring)

**GOOD Examples:**
- "{lead_agent['name']}에게 물어볼게. 이제 각 전공을 기준별로 평가해보자. 점수를 매겨봐."
- "좋아, {lead_agent['name']} 차례야. 전공별 점수를 매겨줘."
- "{lead_agent['name']}, 네 차례야. 학과들을 평가해줘."

**ALL output MUST be in Korean.**
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


def _director_phase_summary(state, finished_agent, next_agent, phase, debate_history):
    """Director가 각 Phase 종료 시 정리 및 다음 Agent 소개"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    current_phase_turns = [t for t in debate_history if f"Phase {phase}" in t.get('phase', '')]
    phase_summary = "\n".join([f"[{t['speaker']}]: {t['content'][:100]}..." for t in current_phase_turns[-4:]])
    
    system_prompt = """You are a friendly debate moderator."""
    
    user_prompt = f"""
{finished_agent['name']} finished their scoring proposal.

Recent discussion:
{phase_summary}

Next agent: {next_agent['name']}

**Write a concise summary (1 sentence) that:**
1. Summarizes ONLY {finished_agent['name']}'s SPECIFIC scoring pattern or key scores (use concrete major-criterion examples)
2. Keep it brief and focused on what was discussed
3. Do NOT introduce or mention {next_agent['name']} - they will be introduced separately

**Tone:** Casual moderator
**Length:** 50-80 characters

**GOOD Example:**
"{finished_agent['name']}는 컴퓨터전공의 기술력을 8.5점으로 평가했네."

**ALL output MUST be in Korean.**
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


def _director_pre_decision_transition(state, personas, debate_history):
    """Director가 최종 결정 전 의견 취합을 알리는 멘트"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    agent_names = [p['name'] for p in personas]
    
    system_prompt = """You are a professional debate moderator wrapping up the discussion."""
    
    user_prompt = f"""
All three agents ({', '.join(agent_names)}) have finished presenting their scoring perspectives.

**Write a brief transition statement that:**
1. Acknowledges that you've heard all agents' opinions
2. Announce that you will now synthesize their input to make a final decision
3. Keep it concise and professional

**Tone:** Moderator wrapping up discussion
**Length:** 50-80 characters

**GOOD Examples:**
- "모든 에이전트들의 의견을 잘 들었어. 이제 의견을 취합해서 최종 점수를 정하겠어."
- "좋아, 세 명의 관점을 모두 들었네. 이제 종합해서 결정을 내려볼게."
- "다들 좋은 의견 고마워. 지금부터 최종 점수를 산출하겠어."

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


def _agent_propose_matrix(state, agent, criteria_names, alternatives, turn, phase):
    """Agent가 전체 Decision Matrix 제안"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    
    user_input = state['user_input']
    selected_criteria = state['selected_criteria']
    
    # 기준별 설명 포함
    criteria_list = "\n".join([
        f"  {i+1}. **{c['name']}**\n     └ {c.get('description', 'N/A')[:150]}..."
        for i, c in enumerate(selected_criteria)
    ])
    
    # 전공 목록
    alternatives_list = "\n".join([f"  - {alt}" for alt in alternatives])
    
    system_prompt = agent['system_prompt']
    
    user_prompt = f"""
User Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Interests:**
{user_input.get('interests', 'N/A')}

**Aptitudes:**
{user_input.get('aptitudes', 'N/A')}

**Core Values:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Majors to evaluate ({len(alternatives)}):
{alternatives_list}

Evaluation criteria ({len(criteria_names)}, selected in Round 1):
{criteria_list}

{SCORING_GUIDE}

---

**Evaluate based on your perspective ({agent.get('perspective', 'Core perspective')}).**

[Important Points]
1. Use user's interests/aptitudes/values as evidence.
2. Explain in format like "For someone with ~ characteristics..."
3. Objectively evaluate what characteristics each major requires for **that criterion**.

[Concrete Evidence Requirements] VERY IMPORTANT
For each key evaluation (2-3), must follow this structure:

**[Major Name] - [Criterion Name]: [Score]**

Evidence (following 3 required):
1. **User Matching**: "User's '[interest/aptitude/value]' matches this major's '[characteristic]'"
2. **Concrete Characteristics**: Mention actual curriculum, job roles, industry characteristics
3. **Score Calculation Logic**: Clear reason why this score

**Improved Examples:**

[BAD]
"컴퓨터공학 - 경제적 성장: 8.5"
"근거: 경제적 전망이 좋아"

[GOOD]
"컴퓨터공학 - 경제적 성장 잠재력: 8.5"
"근거: 
- 사용자가 '높은 연봉'을 명시했고, 컴공은 신입 평균 초봉 5,500만원으로 5개 전공 중 최고야
- '빠른 성장' 원하는 사용자한테 5년차 평균 8,200만원(49% 상승)으로 성장률도 최고
- 사용자의 '코딩 능력 우수'는 고연봉 직무(백엔드, AI)와 바로 연결되니까 8.5점"

"데이터사이언스 - 워라밸: 5.5"
"근거:
- 사용자가 '지속 가능한 커리어'를 언급했는데, 데이터 직무는 마감 압박이 커
- 프로젝트 기반 업무로 주 50-55시간 근무가 일반적이야
- 사용자의 '체계적 계획' 능력은 시간 관리에 도움되지만 구조적 한계로 5.5점"

**작성 형식:**

1. **핵심 평가 2-3개 설명** (각 150-200자로 증가)

각 설명은 다음 구조를 따라:

**[전공명] - [기준명]: [점수]**
근거: [사용자 키워드 인용] + [전공의 구체적 특성] + [점수 산정 논리]

**Evaluation Style - Use diverse patterns:**
Pattern 1 - Strong match: "사용자의 '[특성]'은 이 전공의 '[특성]'과 완벽하게 매칭돼..."
Pattern 2 - Data-driven: "실제로 [통계/연구]를 보면 이 전공은..."
Pattern 3 - Comparative: "다른 전공들과 비교하면 이 전공은..."
Pattern 4 - Limitation awareness: "사용자가 '[특성]'을 원하지만, 이 전공은 [한계]가 있어서..."
Pattern 5 - Potential-based: "사용자의 '[적성]' 능력이 있으면 이 전공에서..."

**작성 예시:**

**컴퓨터공학 - 학문적 깊이와 연구 기회: 7.5**
근거: 논리적 분석과 체계적 사고가 강한 사람한테 컴퓨터공학은 알고리즘, 시스템 설계 등 깊이 있는 학문적 탐구가 가능한 분야야. 연구 기회도 풍부해서 7.5점이 적절해.

**산업디자인 - 안정성과 급여 잠재력: 5.0**
근거: 디자인 분야는 프리랜서 비중이 높아서 초기 급여가 불안정하지만, 경력이 쌓이면 안정화돼. 중간 수준인 5.0점이 적절해.

---

2. **전체 Decision Matrix (JSON 형식)**

위 설명한 2-3개 외에도 **모든 전공 × 모든 기준 조합**에 대해 점수 부여해.

```json
{{
  "decision_matrix": {{
    "{alternatives[0] if alternatives else '전공명'}": {{
      "{criteria_names[0] if criteria_names else '기준명'}": 7.5,
      "{criteria_names[1] if len(criteria_names) > 1 else '기준명2'}": 6.5,
      ...
    }},
    ... (모든 전공에 대해 작성)
  }}
}}
```

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
**ALL your output (explanations, JSON keys, and values) MUST be in Korean.**

**주의사항:**
- 반드시 0.5 단위로만 점수 부여 (1.0, 1.5, 2.0, 2.5, ..., 9.0)
````
- 모든 전공 × 모든 기준 조합 필수 (빠짐없이)
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content
    
    decision_matrix = _extract_decision_matrix(content, alternatives, criteria_names)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {agent['name']} 주도권",
        "speaker": agent['name'],
        "type": "proposal",
        "content": content,
        "decision_matrix": decision_matrix,
        "timestamp": datetime.now().isoformat()
    }


def _agent_critique(state, critic, target_agent, proposal_turn, turn, phase, debate_history):
    """Agent가 다른 Agent의 매트릭스를 반박"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    
    proposed_matrix = proposal_turn.get('decision_matrix', {})
    
    # 매트릭스를 표 형식으로 정리 (샘플만)
    matrix_summary = []
    for major, scores in list(proposed_matrix.items())[:2]:  # 전공 2개만
        matrix_summary.append(f"\n[{major}]")
        for criterion, score in list(scores.items())[:3]:  # 기준 3개만
            matrix_summary.append(f"  - {criterion}: {score}")
        if len(scores) > 3:
            matrix_summary.append(f"  ... 외 {len(scores)-3}개")
    
    matrix_text = "\n".join(matrix_summary)
    
    system_prompt = critic['system_prompt']
    user_prompt = f"""
'{target_agent['name']}'s Decision Matrix Proposal:

{proposal_turn['content'][:500]}...

[Proposed Scores Sample]
{matrix_text}

**Based on your perspective ({critic.get('perspective', '핵심 관점')}), point out the problems.**

[Specific Critique Requirements] ⭐ Very Important

**Critique Target:** Select 2-3 (major-criterion) pairs

**Critique Strategy - Use diverse patterns:**
Pattern 1 - Point out overrating: "○○야, [전공]-[기준] 점수가 너무 높은 것 같아. 사용자가 '[키워드]'를 언급했는데 이 전공은..."
Pattern 2 - Point out underrating: "그 점수는 좀 낮은데? 실제로 [통계/데이터]를 보면..."
Pattern 3 - Challenge logic: "만약 [전제]라면, [결론] 점수가 나와야 하는데 왜 [현재 점수]야?"
Pattern 4 - Comparative critique: "다른 전공들과 비교하면 이 점수는..."
Pattern 5 - Missing perspective: "네 관점에서만 보고 [각도]를 놓친 것 같은데?"

**For each critique, use this structure (mandatory):**

**[Major Name] - [Criterion Name]**
1. **Proposed Score**: X.X
2. **Problem**: [Quote user keywords] + [Present actual major characteristics]
3. **Appropriate Score**: Y.Y
4. **Rationale**: [Specific numbers/ratios/examples] + [Score calculation logic]

**Improved Example:**

❌ Bad critique:
"산업디자인 - 학문적 깊이: 4.5는 과소평가야"

✅ Good critique:
"**산업디자인 - 학문적 깊이와 연구 기회**
- 제안된 점수: 4.5
- 문제점: 사용자가 '체계적 사고'를 언급했는데, 산업디자인의 다학제 연구(인간공학, 재료공학, UX 연구)를 간과했어. 실제 디자인 대학원 연구실 수는 컴공의 70% 수준이야
- 적절한 점수: 6.5
- 근거: 사용자의 '논리적 분석' 강점 + 디자인씽킹 방법론의 체계성 + 석사 진학률 35% = 6.5점"

[Important Points]
1. Quote specific keywords from user's interests/aptitude/values.
2. Mention actual major characteristics (curriculum, industry status, statistics).
3. Provide clear logic for score differences.

---

**Notes:**
- Write logically in 200-250 characters
- Must quote specific user keywords
- Present objective major characteristics or statistics
- Clearly explain score calculation logic

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
**ALL your output MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {target_agent['name']} 주도권",
        "speaker": critic['name'],
        "type": "critique",
        "target": target_agent['name'],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _agent_defend(state, defender, critics, turn, phase, debate_history):
    """Agent가 받은 반박에 재반박"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    
    critiques_received = []
    for turn_data in debate_history:
        if (turn_data['type'] == 'critique' and 
            turn_data['target'] == defender['name'] and
            f"Phase {phase}" in turn_data['phase']):
            critiques_received.append(turn_data)
    
    system_prompt = defender['system_prompt']
    critiques_text = "\n\n".join([f"[{c['speaker']}의 반박]\n{c['content']}" for c in critiques_received])
    
    user_prompt = f"""
Critiques on your Decision Matrix proposal:
{critiques_text}

**Based on your perspective ({defender.get('perspective', '핵심 관점')}), counter-argue.**

**Defense Strategy - Use diverse patterns:**
Pattern 1 - Present overlooked evidence: "○○야, 네가 놓친 게 있어. 사용자가 '[키워드]'도 언급했거든..."
Pattern 2 - Reinterpret same data: "그 데이터를 다르게 해석하면..."
Pattern 3 - Emphasize long-term view: "단기적으로는 그렇지만, 사용자의 5년 후를 생각하면..."
Pattern 4 - Counter with statistics: "실제 [통계]를 보면 내 점수가 합리적이야..."
Pattern 5 - Acknowledge + redirect: "그 부분은 맞아. 하지만 더 중요한 건 사용자의 '[핵심 가치]'인데..."

For each critic:
- Why is your score reasonable?
- What did the critics miss?

Defend logically in 150-250 characters.

**DON'T** use the same defense pattern for every rebuttal
**DO** provide concrete evidence while varying your argumentation style

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
**ALL your output MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {defender['name']} 주도권",
        "speaker": defender['name'],
        "type": "defense",
        "target": [c['name'] for c in critics],
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    }


def _director_final_decision(state, personas, criteria_names, alternatives, debate_history):
    """Director가 토론 내용을 바탕으로 최종 Decision Matrix 결정"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.DIRECTOR_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    
    debate_summary = "\n\n".join([
        f"[Turn {t['turn']} - {t['speaker']} ({t['type']})]"
        f"\n{t['content'][:250]}..."
        for t in debate_history
    ])
    
    proposals = [turn for turn in debate_history if turn['type'] == 'proposal' and turn.get('decision_matrix')]
    proposals_summary = []
    
    for p in proposals:
        proposals_summary.append(f"\n[{p['speaker']}의 제안]")
        matrix = p.get('decision_matrix', {})
        for major, scores in list(matrix.items())[:2]:  # 전공 2개만 샘플
            proposals_summary.append(f"  {major}:")
            for criterion, score in list(scores.items())[:3]:  # 기준 3개만
                proposals_summary.append(f"    - {criterion}: {score}")
    
    proposals_text = "\n".join(proposals_summary)
    
    alternatives_list = "\n".join([f"  {i+1}. {alt}" for i, alt in enumerate(alternatives)])
    criteria_list = "\n".join([f"  {i+1}. {c}" for i, c in enumerate(criteria_names)])
    
    system_prompt = """You are a fair moderator.
Synthesize the Decision Matrix proposals from 3 agents to determine a balanced final matrix.

**Scoring Principles:**

1. **Reflect Debate Consensus Level**
   - All 3 agents propose similar scores → Adopt that score
   - 2 agents similar, 1 different → Weight toward the 2
   - Complete disagreement → Use median or average
   
2. **Ensure Discriminative Power (TOP PRIORITY)**
   - Don't use the same score more than 3 times!
   - Use at least 10 different scores out of 35 evaluations
   - One score should not exceed 30% (max 10 out of 35)
   - Example (WRONG): 6.5 appears 12 times, 7.0 appears 10 times → Lack of discriminative power!
   - Example (CORRECT): 3.5(2), 4.0(3), 4.5(3), 5.0(4), 5.5(3), 6.0(4), 6.5(5), 7.0(5), 7.5(4), 8.0(2) → Diverse
   - Reflect the unique characteristics of each (major-criterion) pair with differentiated scores
   
3. **Score Range & Distribution (Improve Discriminative Power)**
   - Use full range: Difference between min and max must be at least 3.0
   - Top majors (1-3): 6.0-8.0 range (8-9 only for exceptional cases)
   - Middle majors (4-5): 4.5-6.5 range
   - Lower majors (6-7): 3.0-5.5 range (1-2 only for clearly unsuitable cases)
   - Target distribution: Bell curve (most 4-7 points, few extremes)
   - Extreme values: 8-9 and 1-2 should each be within 5% of total
   
4. **Strict 0.5 Unit**
   - Only use 1.0, 1.5, 2.0, ..., 9.0
   
5. **Logical Consistency**
   - Related criteria within same major should have similar score ranges
   - Example: If "aptitude" is high, "job satisfaction" likely high too
   - But don't mechanically give same score - express subtle differences (6.5 vs 7.0)
   
6. **Clear Differentiation Between Majors**
   - Standard deviation of major average scores should be at least 0.5
   - Difference between top and bottom major averages should be at least 1.5
   - Rankings must be clearly distinguished
"""
    
    user_prompt = f"""
Summary of 12 debate turns:
{debate_summary}

Sample proposals from each agent:
{proposals_text}

---

Majors to evaluate:
{alternatives_list}

Evaluation criteria:
{criteria_list}

**Determine the final Decision Matrix.**

Assign scores for all major × criterion combinations,
faithfully reflecting debate content while maintaining score diversity.

Respond in JSON format:

```json
{{
  "decision_matrix": {{
    "전공명": {{
      "기준명": 점수,
      ...
    }},
    ...
  }},
  "reasoning": "점수 결정 이유를 2-3문장으로 설명"
}}
```

**Checklist:**
- [ ] All majors included
- [ ] All criteria included
- [ ] Only 0.5 units used
- [ ] Same score used max 2-3 times (ensure discriminative power!)
- [ ] At least 10 different scores used
- [ ] Full range utilized (min-max difference ≥ 3.0)
- [ ] Clear average difference between majors (std dev ≥ 0.5)

**ALL JSON field values (전공명, 기준명, reasoning) MUST be in Korean.**
"""
    
    user_prompt = f"""
12턴의 토론 요약:
{debate_summary}

각 Agent의 제안 샘플:
{proposals_text}

---

평가 대상 전공:
{alternatives_list}

평가 기준:
{criteria_list}

**최종 Decision Matrix를 결정하세요.**

모든 전공 × 모든 기준 조합에 대해 점수를 부여하되,
토론 내용을 충실히 반영하고 점수 다양성을 유지하세요.

JSON 형식으로 답변:

```json
{{
  "decision_matrix": {{
    "전공명": {{
      "기준명": 점수,
      ...
    }},
    ...
  }},
  "reasoning": "점수 결정 이유를 2-3문장으로 설명"
}}
```

**체크리스트:**
- [ ] 모든 전공 포함됨
- [ ] 모든 기준 포함됨
- [ ] 0.5 단위만 사용
- [ ] 같은 점수 최대 2-3회만 사용 (변별력 확보!)
- [ ] 최소 10개 이상의 서로 다른 점수 사용
- [ ] 전체 범위 활용 (최소-최대 차이 ≥ 3.0)
- [ ] 전공 간 평균 차이가 명확함 (표준편차 ≥ 0.5)
- [ ] 토론 내용 반영
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content
    
    # JSON 파싱
    if '```json' in content:
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
    elif '```' in content:
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
    
    try:
        decision_data = json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 파싱 실패: {e}")
        decision_data = {}
    
    return {
        "turn": len(debate_history) + 1,
        "phase": "Phase 4: Director 최종 결정",
        "speaker": "Director",
        "type": "final_decision",
        "content": content,
        "decision_matrix": decision_data.get('decision_matrix', {}),
        "reasoning": decision_data.get('reasoning', ''),
        "timestamp": datetime.now().isoformat()
    }


def _extract_decision_matrix(content, alternatives, criteria_names):
    """Agent 응답에서 Decision Matrix 추출"""
    # JSON 블록 찾기 (여러 패턴 시도)
    json_text = None
    
    # 패턴 1: ```json ... ``` 블록
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        # 패턴 2: ``` ... ``` 블록
        json_match = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # 패턴 3: 직접 JSON 객체 찾기
            json_match = re.search(r'\{[^}]*"decision_matrix"[^}]*:\s*\{.*?\}\s*\}', content, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
    
    if not json_text:
        print(f"[WARNING] JSON 블록을 찾을 수 없습니다")
        return {}
    
    try:
        # JSON 파싱
        data = json.loads(json_text.strip())
        matrix = data.get('decision_matrix', {})
        
        if not matrix:
            print(f"[WARNING] decision_matrix가 비어있습니다")
            return {}
        
        # 검증: 모든 전공과 기준이 있는지 확인
        for alt in alternatives:
            if alt not in matrix:
                print(f"[WARNING] 전공 '{alt}'가 매트릭스에 없습니다")
                matrix[alt] = {}
            
            for criterion in criteria_names:
                if criterion not in matrix[alt]:
                    print(f"[WARNING] '{alt}' - '{criterion}' 조합이 없습니다. 기본값 5.0 설정")
                    matrix[alt][criterion] = 5.0
        
        print(f"[SUCCESS] JSON 파싱 성공: {len(matrix)}개 전공 × {len(criteria_names)}개 기준")
        return matrix
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 파싱 실패: {e}")
        print(f"시도한 텍스트: {json_text[:200]}...")
        return {}
    except Exception as e:
        print(f"[ERROR] 예외 발생: {e}")
        return {}
