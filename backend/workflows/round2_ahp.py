"""Round 2: 쌍대비교 토론 (13-turn Debate System)"""

import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from itertools import combinations
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config import Config
from utils.ahp_calculator import AHPCalculator
from utils.datetime_utils import get_kst_timestamp


# AHP score scale guide
AHP_SCORE_GUIDE = """
**Score Scale (1-9, 0.5 increments) - How much more important is Criterion A than Criterion B:**

[1.0 - 2.0] Almost equal or minimal difference
- 1.0: Almost equal - Both criteria have similar importance
- 1.5: Very slightly more important - Minimal difference exists
- 2.0: Slightly more important - Small but clear difference

[2.5 - 4.0] Noticeable difference
- 2.5: Somewhat more important - Noticeable difference
- 3.0: Clearly more important - Definite difference
- 3.5: Considerably more important - Large difference
- 4.0: Very important - Very large difference

[4.5 - 6.5] Overwhelming difference
- 4.5: Much more important - Beginning of overwhelming difference
- 5.0: Strongly more important - Clear superiority
- 5.5: Very strongly more important - Firm superiority
- 6.0: Dominantly important - Overwhelming superiority
- 6.5: Extremely important - Incomparable level

[7.0 - 9.0] Extreme difference (use very rarely)
- 7.0: Absolutely important - Complete superiority
- 7.5: Highest level of importance - Extreme superiority
- 8.0: Overwhelmingly important - Nearly incomparable
- 8.5: Extremely important - Completely incomparable
- 9.0: Absolute superiority - Unimaginable difference

**Reciprocals (when B is more important than A):**
- 0.67 (= 1/1.5): B very slightly more
- 0.5 (= 1/2): B slightly more
- 0.4 (= 1/2.5): B somewhat more
- 0.33 (= 1/3): B clearly more
- 0.29 (= 1/3.5): B considerably more
- 0.25 (= 1/4): B very much more
- ... (same pattern continues)

**Score Selection Principles:**
- Consider user's MBTI, values, and goals
- Judge how much more important one criterion is to the user
- Most scores should be within 2-6 range
- Use 7 or above only when there's a very clear and extreme difference
"""


def generate_comparison_pairs(criteria: List[str]) -> List[Tuple[str, str]]:
    """쌍대비교할 기준 쌍 생성"""
    return list(combinations(criteria, 2))


def run_round2_debate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Round 2 토론 시스템 메인 함수 (CR 체크 및 재토론 포함)"""
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
    
    # 비교 쌍 생성
    comparison_pairs = generate_comparison_pairs(criteria_names)
    
    print(f"\n[Round 2] {len(criteria_names)}개 기준 → {len(comparison_pairs)}개 쌍대비교")
    for pair in comparison_pairs:
        print(f"  - {pair[0]} vs {pair[1]}")
    
    # CR threshold 설정
    cr_threshold = state.get('user_input', {}).get('settings', {}).get('cr_threshold', 0.1)
    max_retries = state.get('user_input', {}).get('settings', {}).get('cr_max_retries', 3)
    
    print(f"\n[CR 설정] Threshold: {cr_threshold}, Max Retries: {max_retries}")
    
    # CR이 threshold 이하가 될 때까지 재토론
    for attempt in range(max_retries):
        print(f"\n{'='*60}")
        print(f"[Round 2 Attempt {attempt + 1}/{max_retries}]")
        print(f"{'='*60}")
        
        # 초기화
        debate_turns = []
        
        # Phase 1-3: 각 Agent 주도권
        for phase_idx, lead_agent in enumerate(personas, 1):
            other_agents = [p for p in personas if p['name'] != lead_agent['name']]
            
            # Director 도입 발언 (Phase 시작)
            intro_turn = _director_phase_intro(state, lead_agent, phase_idx, debate_turns)
            debate_turns.append(intro_turn)
            
            # Turn 1: Lead agent 전체 비교표 제안
            proposal_turn = _agent_propose_comparisons(
                state, lead_agent, criteria_names, comparison_pairs,
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
            state, personas, criteria_names, comparison_pairs, debate_turns
        )
        debate_turns.append(director_turn)
        
        # AHP 가중치 계산
        comparison_matrix = director_turn.get('comparison_matrix', {})
        calculator = AHPCalculator()
        
        # 비교 행렬을 AHP 계산기 형식으로 변환
        comparisons = {}
        for pair_key, value in comparison_matrix.items():
            criteria_a, criteria_b = pair_key.split(' vs ')
            comparisons[(criteria_a, criteria_b)] = value
        
        # 쌍대비교 행렬 생성
        pairwise_matrix = calculator.create_pairwise_matrix(criteria_names, comparisons)
        
        # 가중치 계산
        weights_array = calculator.calculate_weights(pairwise_matrix)
        
        # CR 계산
        lambda_max, cr = calculator.calculate_consistency_ratio(pairwise_matrix, weights_array)
        
        # 가중치를 딕셔너리로 변환
        weights = {criteria_names[i]: float(weights_array[i]) for i in range(len(criteria_names))}
        
        print(f"\n[AHP 가중치 계산 완료 - Attempt {attempt + 1}]")
        print(f"  Consistency Ratio: {cr:.4f} (Threshold: {cr_threshold})")
        for criterion, weight in weights.items():
            print(f"  - {criterion}: {weight:.2%}")
        
        # CR이 threshold 이하면 성공
        if cr <= cr_threshold:
            print(f"\n✅ CR이 threshold 이하입니다. 토론 종료.")
            # State 업데이트
            state['round2_debate_turns'] = debate_turns
            state['comparison_matrix'] = comparison_matrix
            state['round2_director_decision'] = director_turn
            state['criteria_weights'] = weights
            state['consistency_ratio'] = float(cr)
            state['eigenvalue_max'] = float(lambda_max)
            state['cr_retry_count'] = attempt + 1
            break
        else:
            print(f"\n⚠️  CR ({cr:.4f})이 threshold ({cr_threshold})를 초과했습니다.")
            if attempt < max_retries - 1:
                print(f"재토론을 시작합니다... (남은 시도: {max_retries - attempt - 1}회)")
                # 재토론을 위해 Director에게 피드백 제공
                state['previous_cr'] = float(cr)
                state['previous_comparison_matrix'] = comparison_matrix
            else:
                print(f"\n❌ 최대 재시도 횟수({max_retries}회)에 도달했습니다. 마지막 결과를 사용합니다.")
                # State 업데이트 (마지막 시도 결과 사용)
                state['round2_debate_turns'] = debate_turns
                state['comparison_matrix'] = comparison_matrix
                state['round2_director_decision'] = director_turn
                state['criteria_weights'] = weights
                state['consistency_ratio'] = float(cr)
                state['eigenvalue_max'] = float(lambda_max)
                state['cr_retry_count'] = max_retries
    
    return state


# Helper functions

def _director_phase_intro(state, lead_agent, phase, debate_history):
    """Director가 각 Phase 시작 시 도입 발언"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    phase_names = ["첫 번째", "두 번째", "세 번째"]
    
    system_prompt = """You are a friendly debate moderator for pairwise comparison discussion."""
    
    user_prompt = f"""
This is the {phase_names[phase-1]} agent's turn for pairwise comparison of evaluation criteria.

Agent: {lead_agent['name']}

**Write a brief introduction (60-100 characters) that:**
1. Introduces {lead_agent['name']} WITHOUT repeating their perspective
2. Asks them to propose comparison scores for criteria pairs
3. Keep it natural and focused on the task (pairwise comparison)

**GOOD Examples:**
- "{lead_agent['name']}에게 물어볼게. 이제 기준들을 서로 비교해볼까? 네 관점에서 점수를 매겨봐."
- "좋아, {lead_agent['name']} 차례야. 각 기준 쌍의 중요도를 비교해줘."
- "{lead_agent['name']}, 네 차례야. 기준들의 상대적 중요도를 평가해줘."

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
        "timestamp": get_kst_timestamp()
    }


def _director_phase_summary(state, finished_agent, next_agent, phase, debate_history):
    """Director가 각 Phase 종료 시 정리 및 다음 Agent 소개"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    current_phase_turns = [t for t in debate_history if f"Phase {phase}" in t.get('phase', '')]
    phase_summary = "\n".join([f"[{t['speaker']}]: {t['content'][:100]}..." for t in current_phase_turns[-4:]])
    
    system_prompt = """You are a friendly debate moderator. Your role is to summarize what was discussed with rich context and insight."""
    
    user_prompt = f"""
{finished_agent['name']} just finished presenting their pairwise comparison approach.

Recent discussion:
{phase_summary}

Next agent: {next_agent['name']}

**Write a rich summary (2-3 sentences) that:**
1. Summarizes the SPECIFIC comparison logic and key scores {finished_agent['name']} proposed (use concrete examples)
2. Explain the REASONING/LOGIC behind the pairwise comparisons - WHY these scores matter, what logic or evidence was used
3. Connect to USER's characteristics or goals mentioned in the discussion
4. Highlight what makes {finished_agent['name']}'s perspective unique
5. Do NOT introduce or mention {next_agent['name']} - they will be introduced separately

**Tone:** Casual moderator providing insightful commentary
**Length:** 150-250 characters

**GOOD Example:**
"{finished_agent['name']}는 '경제성'과 '창의성'을 비교할 때, 사용자의 실용적 성향을 반영해 경제성에 더 높은 점수를 줬어. 논리적 근거와 실제 사례를 들어 쌍대비교의 타당성을 강조했네."

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
        "timestamp": get_kst_timestamp()
    }


def _director_pre_decision_transition(state, personas, debate_history):
    """Director가 최종 결정 전 의견 취합을 알리는 멘트"""
    llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0.7, api_key=Config.OPENAI_API_KEY)
    
    agent_names = [p['name'] for p in personas]
    
    system_prompt = """You are a professional debate moderator wrapping up the discussion."""
    
    user_prompt = f"""
All three agents ({', '.join(agent_names)}) have finished presenting their pairwise comparison perspectives.

**Write a brief transition statement that:**
1. Acknowledges that you've heard all agents' opinions
2. Announce that you will now synthesize their input to make a final decision
3. Keep it concise and professional

**Tone:** Moderator wrapping up discussion
**Length:** 50-80 characters

**GOOD Examples:**
- "모든 에이전트들의 의견을 잘 들었어. 이제 의견을 취합해서 최종 비교표를 정하겠어."
- "좋아, 세 명의 관점을 모두 들었네. 이제 종합해서 결정을 내려볼게."
- "다들 좋은 의견 고마워. 지금부터 최종 가중치를 산출하겠어."

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
        "timestamp": get_kst_timestamp()
    }


def _agent_propose_comparisons(state, agent, criteria, pairs, turn, phase):
    """Agent가 전체 쌍대비교표 제안"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    user_input = state['user_input']
    majors = user_input['candidate_majors']  # alternatives 대신 직접 사용
    
    pairs_text = "\n".join([f"  {i+1}. {a} vs {b}" for i, (a, b) in enumerate(pairs)])
    system_prompt = agent['system_prompt']
    
    user_prompt = f"""
{len(criteria)} evaluation criteria selected in Round 1: {', '.join(criteria)}

These criteria need to be pairwise compared (total {len(pairs)} pairs):
{pairs_text}

User Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Interests:**
{user_input.get('interests', 'N/A')}

**Aptitudes:**
{user_input.get('aptitudes', 'N/A')}

**Core Values:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Evaluate pairwise comparisons based on your perspective ({agent.get('perspective', 'Core perspective')}).**

[Important Points]
1. Don't mention specific majors, only compare the importance of criteria themselves.
2. Actively use user's interests/aptitudes/values as evidence.
3. Explain in format like "For someone with ~ characteristics..."

[Concrete Rebuttal Requirements] VERY IMPORTANT

**Critique target:** 2-3 specific scores (not all)

**For each score, this structure is REQUIRED:**

**[Criterion A] vs [Criterion B]: proposed score**
- Problems: Why overrated/underrated + Quote user keywords
- Appropriate score: Suggest alternative score
- Rationale: Specific evidence + Scoring logic

[BAD] "This score is overrated" (no evidence)
[GOOD] "3.0 is overrated. User used the word 'sustainable', which means valuing work-life balance, so 1.5 is appropriate"

{AHP_SCORE_GUIDE}

**Evaluation Method:**
For each pair, judge "How much more important is A than B?"
- If A is more important: 1.5 ~ 9.0
- Almost equal: 1.0
- If B is more important: use reciprocal (0.67, 0.5, 0.33, etc.)

**Examples:**
- "Economic success vs Work-life balance": Those wanting fast growth prioritize economic success → 2.5
- "Work-life balance vs Social contribution": Those valuing sustainability prioritize work-life balance → 3.0

**How to present your evaluation:**
1. Explain 3-4 key comparisons naturally in conversation style
2. Connect to user's specific characteristics (quote their words)
3. Provide concrete evidence for each score
4. At the end, provide **all {len(pairs)} pairs** in JSON format

**Conversation Pattern Examples:**
- "내 관점에서 보면 [기준A]가 [기준B]보다 훨씬 중요해. 왜냐하면 사용자가 '[키워드]'라고 했잖아..."
- "[기준A] vs [기준B]는 솔직히 비슷한 수준이야. 둘 다 [이유]..."
- "[기준A]는 [기준B]의 3배 정도 중요하다고 봐. 실제로 [데이터/사례]..."

```json
{{"comparison_matrix": {{"기준A vs 기준B": number, ...}}}}
```

**DON'T** write mechanically like a report
**DO** speak naturally while including evidence and reasoning

**Tone Reminder**: Write casually as if talking to a friend. Use informal Korean (반말) naturally!
**ALL your output (explanations and JSON keys) MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content
    
    comparison_matrix = _extract_comparison_matrix(content, pairs)
    
    return {
        "turn": turn,
        "phase": f"Phase {phase}: {agent['name']} 주도권",
        "speaker": agent['name'],
        "type": "proposal",
        "content": content,
        "comparison_matrix": comparison_matrix,
        "timestamp": get_kst_timestamp()
    }


def _agent_critique(state, critic, target_agent, proposal_turn, turn, phase, debate_history):
    """Agent가 다른 Agent의 비교표를 반박"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )
    
    proposed_matrix = proposal_turn.get('comparison_matrix', {})
    matrix_text = "\n".join([f"  - {pair}: {value}" for pair, value in proposed_matrix.items()])
    
    system_prompt = critic['system_prompt']
    user_prompt = f"""
'{target_agent['name']}'s pairwise comparison proposal:
{proposal_turn['content'][:400]}...

[Proposed Comparison Table]
{matrix_text}

**Point out problems based on your perspective ({critic.get('perspective', 'Core perspective')}).**

[Concrete Rebuttal Requirements] ⭐ Very Important
Point out 2-3 most problematic pairs, and for each must include:

1. **State proposed score**: "X vs Y: 3.0"
2. **Specify the problem**: 
   - Which part of the user did they miss?
   - What logical contradiction exists?
3. **Alternative score + evidence**:
   e.g., "1.5 is appropriate. Because user mentioned 'work-life balance' 2 times and 'fast growth' 3 times, so 3:2 = 1.5x"
   e.g., "4.0 is reasonable. User's mention of 'global company' means prioritizing economic growth 4x more"

❌ Bad rebuttal: "This score is overrated" (no evidence)
✅ Good rebuttal: "3.0 is overrated. User used the word 'sustainable', which means valuing work-life balance, so 1.5 is appropriate"

**Critique Strategy - Use diverse patterns:**
Pattern 1 - Point out missed evidence: "○○야, 근데 사용자가 '[키워드]'를 3번이나 언급했어. 그럼 [점수] 정도는 되어야지"
Pattern 2 - Challenge with data: "그 점수는 좀 이상한데? [통계/사례]를 보면..."
Pattern 3 - Contrast perspectives: "네 관점에선 그럴 수 있지만, [다른 각도]에서 보면..."
Pattern 4 - Logical contradiction: "만약 [전제]라면, [모순] 문제가 생기는데?"
Pattern 5 - Suggest alternative: "차라리 [대안 점수]가 더 합리적일 것 같아. 왜냐하면..."

**Score Selection Guide:**
  1.0-2.0: Subtle difference 
  2.5-4.0: Noticeable difference
  4.5-6.5: Overwhelming difference
  7.0-9.0: Extreme difference (very rare)

Rebut logically in 150-250 characters.

**DON'T** use the same critique pattern repeatedly
**DO** vary your argumentation style while providing concrete evidence

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
        "timestamp": get_kst_timestamp()
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
Rebuttals to your pairwise comparison proposal:
{critiques_text}

**Counter-rebut based on your perspective ({defender.get('perspective', 'Core perspective')}).**

[Concrete Defense Requirements] VERY IMPORTANT
For each rebuttal, must include:

1. **Name the rebuttor**: "{critics[0]['name']}야..." or "{critics[0]['name']} 말은..."
2. **Summarize their argument**: "...라고 했지만"
3. **Concrete counter-rebuttal**:
   - Present different aspects of user information
   - Point out keywords or context they missed
   - Rebut with numbers (e.g., "3 mentions vs 1 mention", "70% vs 30%", etc.)

**Defense Strategy - Use diverse patterns:**
Pattern 1 - Counter with different evidence: "○○야, 네 말도 맞는데 [다른 증거]도 봐봐. 사용자가..."
Pattern 2 - Show bigger context: "단기적으로는 그렇지만, 장기적으로 보면..."
Pattern 3 - Reinterpret same data: "그 키워드를 다르게 해석하면..."
Pattern 4 - Numerical rebuttal: "사용자는 'A'를 3번, 'B'를 1번 언급했어. 3:1 비율이면..."
Pattern 5 - Acknowledge + redirect: "그 부분은 인정해. 하지만 더 중요한 건..."

**Example:**
"{critics[0]['name']}가 워라밸을 강조했지만, 사용자는 '높은 연봉'을 3번, '빠른 성장'을 2번 언급한 반면 '워라밸'은 1번만 언급했어. 이건 5:1 비율로 경제적 성장을 우선시한다는 뜻이야"

While mentioning each rebuttor:
- Why your score is reasonable
- What the rebuttors missed in their arguments

Defend logically in 150-250 characters.

**DON'T** use the same defense pattern for every rebuttal
**DO** vary your argumentation while staying consistent to your perspective

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
        "timestamp": get_kst_timestamp()
    }


def _director_final_decision(state, personas, criteria, pairs, debate_history):
    """Director가 토론 내용을 바탕으로 최종 비교 행렬 결정"""
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        temperature=Config.DIRECTOR_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY,
        max_tokens=2000  # 비교 행렬 JSON이 잘리지 않도록
    )
    
    debate_summary = "\n\n".join([
        f"[Turn {t['turn']} - {t['speaker']} ({t['type']})]"
        f"\n{t['content'][:250]}..."
        for t in debate_history
    ])
    
    proposals = [turn for turn in debate_history if turn['type'] == 'proposal' and turn.get('comparison_matrix')]
    proposals_text = "\n\n".join([
        f"[{p['speaker']}의 제안]\n" + 
        "\n".join([f"  {pair}: {value}" for pair, value in list(p['comparison_matrix'].items())[:5]])
        for p in proposals
    ])
    
    pairs_text = "\n".join([f"  {i+1}. {a} vs {b}" for i, (a, b) in enumerate(pairs)])
    
    system_prompt = """You are a fair moderator. 
Synthesize the positions of the 3 Agents to determine a balanced final comparison matrix.

[Evidence-Based Decision Principles] VERY IMPORTANT

1. **Evaluate Agent Arguments' Evidence**:
   - Higher weight for arguments citing user keywords
   - Prioritize arguments presenting specific numbers/ratios
   - Lower weight for abstract arguments ("it's important")

2. **Direct Analysis of User Input**:
   - Count keyword frequency related to each criterion
   - e.g., "high salary" 3 times, "work-life balance" 1 time → 3:1 = 3.0
   - Add +0.5 if emphasis expressions ("very", "really", "especially") present

3. **Score Decision Logic**:
   - Convert keyword frequency ratio to score
   - Adjust considering Agent consensus
   - Final score = (keyword ratio × 0.7) + (Agent consensus × 0.3)

Score Decision Principles:
1. **Clear Distinction by Score**:
   - 1-2: Almost similar or subtle difference
   - 2.5-4: Noticeable difference, one clearly more important
   - 4.5-6.5: Big difference, one overwhelmingly important
   - 7-9: Extreme difference, incomparable level

2. **Based on Debate Consensus**:
   - 3 Agents mostly agree: Clear value (6-8 or 1/6-1/8)
   - 2 agree, 1 opposes: Medium~strong value (4-6 or 1/4-1/6)
   - Opinions split: Normal value (2-4)
   - Complete opposition: Neutral value (1-1.5)

3. **Must use 0.5 increments**: 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9

4. **Ensure Discrimination (Top Priority)**: 
   - Don't use same score more than 3 times!
   - 10 pairs should receive at least 7 different scores
   - One score shouldn't exceed 20% (max 2 out of 10)
   - Example (wrong): 3.5 four times, 4.0 three times → lack diversity!
   - Example (correct): 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5 → all different
   - Assign differentiated scores reflecting each pair's unique characteristics

5. **Actively Use Full Score Range (Improve Discrimination)**: 
   - Use the full 1-9 scale widely! Don't cluster only in 2-4 range
   - Target: difference between min and max should be at least 3.0
   
6. **Score Range Guide by Consensus Level**:
   - All 3 Agents strongly agree (clear advantage): Use 6.0-8.0 range
   - 2 agree, 1 opposes (normal advantage): Use 3.5-5.5 range
   - Opinions split (weak advantage): Use 2.0-3.0 range
   - Complete opposition or neutral (almost equal): Use 1.0-1.5 range
   - Target distribution: mostly 3-6 points, 1-2 and 7-9 only for extreme cases"""

    user_prompt = f"""
12 turns of debate:
{debate_summary}

Each Agent's proposal:
{proposals_text}

Decide final comparison values for the following {len(pairs)} pairs:
{pairs_text}

**Accurately understand the meaning of each score and use balanced values reflecting the debate content.**

**Score Guide (0.5 increments):**
- 1: Almost equal
- 1.5-2: Very slightly/somewhat more important
- 2.5-3: Slightly/clearly more important
- 3.5-4: Considerably/very important
- 4.5-5: Much/strongly more important
- 5.5-6: Very strongly/dominantly important
- 6.5-7: Extremely/absolutely important
- 7.5-9: Highest level/overwhelming advantage (use rarely)

**Required: Use Wide Score Range**
- Use the full 1-9 scale evenly
- All scores shouldn't cluster in similar range (e.g., 2-4)
- If there was strong consensus in debate, actively use high scores of 5.0 or above
- If opinions are similar or opposed, also use low scores (1.0-2.0)
- Clearly distinguish importance differences of each pair through score range

**Convert Debate Content to Scores:**
- All 3 Agents agree → Use **6-8**
- 2 Agents strongly agree → Use **4-6**
- 2 Agents weakly agree → Use **3-4**
- Opinions split → Use **2-3**
- 2 Agents oppose → Use **1-2** (use reciprocal)

**Concrete Examples:**
- "A is absolutely important" (3 agents agree) → 7.0
- "A is much more important" (2 agents agree) → 5.0
- "A is slightly more important" (opinions split) → 2.5
- "Almost similar" (complete opposition) → 1.0

Reciprocal examples: 1/2=0.5, 1/3=0.33, 1/4=0.25, 1/5=0.2, 1/6=0.17, 1/7=0.14

Answer in JSON format:
```json
{{"comparison_matrix": {{"기준A vs 기준B": number, ...}}, "reasoning": "Explanation of each score decision"}}
```
**ALL field values (keys and reasoning) MUST be in Korean.**
"""
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content
    
    # JSON 파싱 전 전처리
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
        print(f"[SUCCESS] Round 2 Director final decision JSON 파싱 성공")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Round 2 JSON 파싱 실패: {e}")
        print(f"[ERROR] 실패한 내용 (첫 500자): {content[:500]}")
        decision_data = {}
    
    return {
        "turn": len(debate_history) + 1,
        "phase": "Phase 4: Director 최종 결정",
        "speaker": "Director",
        "type": "final_decision",
        "content": content,
        "comparison_matrix": decision_data.get('comparison_matrix', {}),
        "reasoning": decision_data.get('reasoning', ''),
        "timestamp": get_kst_timestamp()
    }


def _extract_comparison_matrix(content, pairs):
    """Agent 응답에서 비교 행렬 추출"""
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
            json_match = re.search(r'\{[^}]*"comparison_matrix"[^}]*:\s*\{[^}]*\}[^}]*\}', content, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
    
    if not json_text:
        print(f"[WARNING] JSON 블록을 찾을 수 없습니다")
        return {}
    
    try:
        # JSON 파싱
        data = json.loads(json_text.strip())
        matrix = data.get('comparison_matrix', {})
        
        if not matrix:
            print(f"[WARNING] comparison_matrix가 비어있습니다")
            return {}
        
        # 쌍 형식 표준화
        standardized = {}
        for pair in pairs:
            key1 = f"{pair[0]} vs {pair[1]}"
            key2 = f"{pair[1]} vs {pair[0]}"
            
            if key1 in matrix:
                val = float(matrix[key1])
                standardized[key1] = val
            elif key2 in matrix:
                val = float(matrix[key2])
                standardized[key1] = 1/val if val != 0 else 1.0
            else:
                # 기본값: 중립
                standardized[key1] = 1.0
        
        print(f"[SUCCESS] JSON 파싱 성공: {len(standardized)}개 쌍")
        return standardized
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 파싱 실패: {e}")
        print(f"시도한 텍스트: {json_text[:200]}...")
        return {}
    except Exception as e:
        print(f"[ERROR] 예외 발생: {e}")
        return {}

