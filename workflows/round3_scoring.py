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


# Decision Matrix 점수 척도 가이드
SCORING_GUIDE = """
**점수 척도 (1-9, 0.5 단위) - 각 전공이 각 기준에서 얼마나 적합한가:**

[1.0 - 3.0] 부적합 구간
- 1.0: 매우 부적합 - 이 전공은 해당 기준에서 전혀 맞지 않음
- 1.5: 거의 부적합 - 거의 모든 측면에서 맞지 않음
- 2.0: 부적합 - 여러 측면에서 맞지 않음
- 2.5: 약간 부적합 - 일부 측면에서 맞지 않음
- 3.0: 다소 부적합 - 부족한 점이 눈에 띔

[3.5 - 5.5] 보통 구간
- 3.5: 보통 이하 - 기대에 조금 못 미침
- 4.0: 보통 - 무난한 수준
- 4.5: 보통 이상 - 기대를 조금 상회
- 5.0: 적합 - 기준을 충분히 만족
- 5.5: 상당히 적합 - 기준을 잘 만족

[6.0 - 9.0] 적합 구간
- 6.0: 매우 적합 - 기준에 아주 잘 부합
- 6.5: 아주 적합 - 기준을 크게 상회
- 7.0: 탁월하게 적합 - 매우 훌륭한 선택
- 7.5: 매우 탁월하게 적합 - 거의 이상적
- 8.0: 거의 이상적 - 완벽에 가까움
- 8.5: 거의 완벽 - 흠잡을 데 없음
- 9.0: 완벽하게 적합 - 더 이상 바랄 것 없음

**점수 선택 기준:**
- 사용자의 MBTI 성향과 전공의 특성이 얼마나 일치하는가?
- 사용자의 강점이 해당 전공에서 발휘될 가능성은?
- 사용자가 중요하게 생각하는 가치가 이 전공에서 실현될 가능성은?
- 객관적 데이터(취업률, 급여, 워라밸 등)는 어떠한가?

**점수 분포 가이드:**
- 8-9점: 정말 예외적으로 완벽한 경우만 (매우 드물게)
- 1-2점: 명백히 부적합한 경우만 (매우 드물게)
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
사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미:**
{user_input.get('interests', 'N/A')}

**적성:**
{user_input.get('aptitudes', 'N/A')}

**추구 가치:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

평가 대상 전공 ({len(alternatives)}개):
{alternatives_list}

평가 기준 ({len(criteria_names)}개, Round 1에서 선정):
{criteria_list}

{SCORING_GUIDE}

---

**당신의 관점({agent.get('perspective', '핵심 관점')})을 바탕으로 평가하세요.**

[중요 지침]
1. 사용자의 흥미/적성/가치관을 근거로 제시하세요.
2. "~한 특성을 가진 사람에게는..." 형식으로 설명하세요.
3. 각 전공이 **해당 기준**에서 어떤 특성을 요구하는지 객관적으로 평가하세요.

**작성 형식:**

1. **핵심 평가 2-3개 설명** (각 100-150자)

각 설명은 다음 구조를 따르세요:

**[전공명] - [기준명]: [점수]**
근거: [사용자의 특성]을 가진 사람에게 이 전공은 [기준 관점에서의 특성]하므로 [점수]를 부여합니다.

**작성 예시:**

**컴퓨터공학 - 학문적 깊이와 연구 기회: 7.5**
근거: 논리적 분석과 체계적 사고가 강한 사람에게 컴퓨터공학은 알고리즘, 시스템 설계 등 깊이 있는 학문적 탐구가 가능한 분야입니다. 연구 기회도 풍부하여 7.5점이 적절합니다.

**산업디자인 - 안정성과 급여 잠재력: 5.0**
근거: 디자인 분야는 프리랜서 비중이 높아 초기 급여가 불안정하지만, 경력이 쌓이면 안정화됩니다. 중간 수준인 5.0점이 적절합니다.

---

2. **전체 Decision Matrix (JSON 형식)**

위 설명한 2-3개 외에도 **모든 전공 × 모든 기준 조합**에 대해 점수를 부여하세요.

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
'{target_agent['name']}'의 Decision Matrix 제안:

{proposal_turn['content'][:500]}...

[제안된 점수 샘플]
{matrix_text}

**당신의 관점({critic.get('perspective', '핵심 관점')})을 바탕으로 문제점을 지적하세요.**

[중요 지침]
1. 사용자의 MBTI 성향은 참고만 하되, 발언에서는 직접 언급하지 마세요.
2. 대신 사용자의 구체적 특성(강점/약점)을 근거로 제시하세요.
3. 각 전공이 **해당 기준**에서 어떤 객관적 특성을 갖는지 설명하세요.

**지적 대상:** 2-3개의 (전공-기준) 쌍을 선택

**각 지적마다 다음 구조로 작성:**

**[전공명] - [기준명]의 점수 문제**
1. **제안된 점수**: [상대방이 제안한 점수]
2. **문제점**: [왜 이 점수가 부적절한지 객관적으로 설명]
3. **적절한 점수**: [당신이 생각하는 적절한 점수] (0.5 단위)
4. **근거**: [사용자의 특성(강점/약점)을 고려할 때 왜 이 점수가 더 합리적인지]

**작성 예시:**

**산업디자인 - 학문적 깊이와 연구 기회**
- 제안된 점수: 4.5
- 문제점: 디자인 분야의 학문적 깊이를 과소평가했습니다. 산업디자인은 인간공학, 재료공학, 심리학 등 다학제적 연구가 활발합니다.
- 적절한 점수: 6.5
- 근거: 논리적 분석과 체계적 사고가 강한 사람에게 산업디자인의 연구 기회는 충분히 매력적입니다. 디자인 씽킹과 사용자 연구 등 체계적 방법론이 발달해 있어 6.5점이 적절합니다.

---

**주의사항:**
- 150-200자로 논리적으로 반박
- 반드시 사용자의 구체적 특성(강점/약점)을 언급
- 단순 의견 차이가 아닌 객관적 근거 제시
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
당신의 Decision Matrix 제안에 대한 반박:
{critiques_text}

**당신의 관점({defender.get('perspective', '핵심 관점')})을 바탕으로 재반박하세요.**

각 반박자를 언급하며:
- 왜 당신의 점수가 합리적인지
- 반박자들의 주장에서 놓친 부분은 무엇인지

150-250자로 논리적으로 방어하세요.
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
    
    system_prompt = """당신은 공정한 중재자입니다.
3명 Agent의 Decision Matrix 제안을 종합하여 균형잡힌 최종 매트릭스를 결정하세요.

**점수 결정 원칙:**

1. **토론 합의 수준 반영**
   - 3명 모두 비슷한 점수 제안 → 그 점수 채택
   - 2명이 유사, 1명만 다름 → 2명 쪽에 가중치
   - 완전히 의견 갈림 → 중간값 또는 평균
   
2. **변별력 확보 (최우선 원칙)**
   - 같은 점수를 3번 이상 사용하지 마세요!
   - 35개 평가 중 최소 10개 이상의 서로 다른 점수를 사용하세요
   - 하나의 점수가 30%를 초과하면 안 됩니다 (35개 중 최대 10개까지만)
   - 예시 (잘못됨): 6.5가 12개, 7.0이 10개 → 변별력 부족!
   - 예시 (올바름): 3.5(2), 4.0(3), 4.5(3), 5.0(4), 5.5(3), 6.0(4), 6.5(5), 7.0(5), 7.5(4), 8.0(2) → 다양함
   - 각 (전공-기준) 쌍의 고유한 특성을 반영하여 차별화된 점수를 부여하세요
   
3. **점수 범위 및 분포 (변별력 향상)**
   - 전체 범위 활용: 최소값과 최대값의 차이가 최소 3.0 이상 되어야 합니다
   - 우수 전공 (1-3위): 6.0-8.0 범위 (8-9는 정말 예외적인 경우만)
   - 중간 전공 (4-5위): 4.5-6.5 범위
   - 하위 전공 (6-7위): 3.0-5.5 범위 (1-2는 명백히 부적합한 경우만)
   - 목표 분포: 종 모양 곡선 (대부분 4-7점, 양 극단은 소수)
   - 극단값 사용: 8-9점과 1-2점은 각각 전체의 5% 이내
   
4. **0.5 단위 엄수**
   - 반드시 1.0, 1.5, 2.0, ..., 9.0만 사용
   
5. **논리적 일관성**
   - 같은 전공 내에서 관련 기준들은 유사한 점수대
   - 예: "적성"이 높으면 "직무 만족도"도 높을 가능성
   - 단, 기계적으로 같은 점수를 주지 말고 미묘한 차이를 표현하세요 (6.5 vs 7.0)
   
6. **전공 간 명확한 차별화**
   - 전공 평균 점수의 표준편차가 최소 0.5 이상 되도록 하세요
   - 최고 전공과 최하위 전공의 평균 차이가 최소 1.5 이상
   - 순위가 명확히 구분되어야 합니다
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
