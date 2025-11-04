"""Round 2: 쌍대비교 토론 (13-turn Debate System)"""

import yaml
import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime
from itertools import combinations
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config import Config
from utils.ahp_calculator import AHPCalculator


# AHP 점수 척도 가이드
AHP_SCORE_GUIDE = """
**점수 척도 (1-9, 0.5 단위) - 기준 A가 기준 B보다 얼마나 더 중요한가:**

[1.0 - 2.0] 거의 동등하거나 미세한 차이
- 1.0: 거의 동등 - 두 기준이 거의 같은 중요도
- 1.5: 아주 약간 더 중요 - 미세한 차이만 존재
- 2.0: 조금 더 중요 - 작지만 명확한 차이

[2.5 - 4.0] 눈에 띄는 차이
- 2.5: 약간 더 중요 - 눈에 띄는 차이가 있음
- 3.0: 분명히 더 중요 - 확실한 차이가 있음
- 3.5: 상당히 더 중요 - 큰 차이가 있음
- 4.0: 매우 중요 - 매우 큰 차이

[4.5 - 6.5] 압도적인 차이
- 4.5: 훨씬 더 중요 - 압도적 차이의 시작
- 5.0: 강하게 더 중요 - 명백한 우위
- 5.5: 매우 강하게 더 중요 - 확고한 우위
- 6.0: 지배적으로 중요 - 압도적 우위
- 6.5: 극도로 중요 - 비교 불가 수준

[7.0 - 9.0] 극단적 차이 (매우 드물게 사용)
- 7.0: 절대적으로 중요 - 완전한 우위
- 7.5: 최고 수준으로 중요 - 극단적 우위
- 8.0: 압도적으로 중요 - 거의 비교 불가
- 8.5: 극단적으로 중요 - 완전 비교 불가
- 9.0: 절대 우위 - 상상할 수 없는 차이

**역수 (B가 A보다 중요한 경우):**
- 0.67 (= 1/1.5): B가 아주 약간 더
- 0.5 (= 1/2): B가 조금 더
- 0.4 (= 1/2.5): B가 약간 더
- 0.33 (= 1/3): B가 분명히 더
- 0.29 (= 1/3.5): B가 상당히 더
- 0.25 (= 1/4): B가 매우 더
- ... (이하 동일 패턴)

**점수 선택 원칙:**
- 사용자의 MBTI, 가치관, 목표를 고려
- 두 기준 중 하나가 사용자에게 얼마나 더 중요한지 판단
- 대부분의 점수는 2-6 범위 내에 있어야 함
- 7 이상은 매우 명확하고 극단적인 차이가 있을 때만 사용
"""


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_comparison_pairs(criteria: List[str]) -> List[Tuple[str, str]]:
    """쌍대비교할 기준 쌍 생성"""
    return list(combinations(criteria, 2))


def run_round2_debate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Round 2 토론 시스템 메인 함수 (13턴 구조)"""
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
    
    # 초기화
    debate_turns = []
    
    # Phase 1-3: 각 Agent 주도권
    for phase_idx, lead_agent in enumerate(personas, 1):
        other_agents = [p for p in personas if p['name'] != lead_agent['name']]
        
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
    
    # Phase 4: Director 최종 결정
    director_turn = _director_final_decision(
        state, personas, criteria_names, comparison_pairs, debate_turns
    )
    debate_turns.append(director_turn)
    
    # State 업데이트
    state['round2_debate_turns'] = debate_turns
    state['comparison_matrix'] = director_turn.get('comparison_matrix', {})
    state['round2_director_decision'] = director_turn
    
    # AHP 가중치 계산
    comparison_matrix = state['comparison_matrix']
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
    
    # State에 결과 저장
    state['criteria_weights'] = weights
    state['consistency_ratio'] = float(cr)
    state['eigenvalue_max'] = float(lambda_max)
    
    print(f"\n[AHP 가중치 계산 완료]")
    print(f"  Consistency Ratio: {cr:.4f}")
    print(f"  Lambda Max: {lambda_max:.4f}")
    print(f"\n[기준별 가중치]")
    for criterion, weight in weights.items():
        print(f"  - {criterion}: {weight:.4f}")
    
    return state


# Helper functions
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
Round 1에서 선정된 {len(criteria)}개 평가 기준: {', '.join(criteria)}

이 기준들을 쌍대비교해야 합니다 (총 {len(pairs)}개 쌍):
{pairs_text}

사용자 특성:
- 강점: {', '.join(user_input.get('strengths', []))}
- 약점: {', '.join(user_input.get('weaknesses', []))}
- 핵심 가치관: {', '.join(user_input.get('core_values', []))}

**당신의 핵심 가치({', '.join(agent['core_values'])})를 바탕으로 쌍대비교를 평가하세요.**

[중요 지침]
1. 특정 학과나 전공을 언급하지 마세요. 기준 자체의 중요성만 비교하세요.
2. 사용자의 MBTI 성향은 참고만 하되, 발언에서는 직접 언급하지 마세요.
3. 사용자의 구체적 특성(강점/약점/가치관)을 적극적으로 근거로 활용하세요.
4. "~한 특성을 가진 사람에게는..." 형식으로 설명하세요.

{AHP_SCORE_GUIDE}

**평가 방법:**
각 쌍을 비교할 때, "A가 B보다 얼마나 더 중요한가?"를 판단하세요.
- A가 더 중요하면: 1.5 ~ 9.0
- 거의 동등하면: 1.0
- B가 더 중요하면: 역수 사용 (0.67, 0.5, 0.33 등)

**예시:**
- "적성 vs 급여": 체계적 사고가 강한 사람은 적성 일치를 더 중시 → 2.5
- "워라밸 vs 사회공헌": 책임감이 강한 사람은 워라밸이 더 중요 → 3.0

핵심 비교 3-4개만 간단히 설명하고, 마지막에 JSON 형식으로 **전체 {len(pairs)}개 쌍** 비교표를 제공하세요:

```json
{{"comparison_matrix": {{"기준A vs 기준B": 숫자, ...}}}}
```
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
        "timestamp": datetime.now().isoformat()
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
'{target_agent['name']}'의 쌍대비교 제안:
{proposal_turn['content'][:400]}...

[제안된 비교표]
{matrix_text}

**당신의 핵심 가치({', '.join(critic['core_values'])})를 바탕으로 문제점을 지적하세요.**

가장 문제가 되는 2-3개 쌍을 지적하며:
- 왜 점수가 적절하지 않은지
- 당신의 관점에서는 어떤 점수가 더 합리적인지 **(0.5 단위로 제시)**
  
**점수 선택 가이드:**
  1.0-2.0: 미세한 차이 
  2.5-4.0: 눈에 띄는 차이
  4.5-6.5: 압도적 차이
  7.0-9.0: 극단적 차이 (매우 드물게)
  
  예: "이 쌍은 6.5(극도로 중요) 정도가 적절합니다"
      "1.5(아주 약간 차이)로 평가하는 것이 합리적입니다"

150-250자로 논리적으로 반박하세요.
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
당신의 쌍대비교 제안에 대한 반박:
{critiques_text}

**당신의 핵심 가치({', '.join(defender['core_values'])})를 바탕으로 재반박하세요.**

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


def _director_final_decision(state, personas, criteria, pairs, debate_history):
    """Director가 토론 내용을 바탕으로 최종 비교 행렬 결정"""
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
    
    proposals = [turn for turn in debate_history if turn['type'] == 'proposal' and turn.get('comparison_matrix')]
    proposals_text = "\n\n".join([
        f"[{p['speaker']}의 제안]\n" + 
        "\n".join([f"  {pair}: {value}" for pair, value in list(p['comparison_matrix'].items())[:5]])
        for p in proposals
    ])
    
    pairs_text = "\n".join([f"  {i+1}. {a} vs {b}" for i, (a, b) in enumerate(pairs)])
    
    system_prompt = """당신은 공정한 중재자입니다. 
3명 Agent의 입장을 종합하여, 균형잡힌 최종 비교 행렬을 결정하세요.

점수 결정 원칙:
1. **점수별 명확한 의미 구분**:
   - 1-2: 거의 비슷하거나 미세한 차이
   - 2.5-4: 눈에 띄는 차이, 하나가 분명히 더 중요
   - 4.5-6.5: 큰 차이, 하나가 압도적으로 중요
   - 7-9: 극단적 차이, 비교 불가능한 수준

2. **토론 합의 수준에 따라**:
   - 3명 대부분 동의: 명확한 값 (6-8 또는 1/6-1/8)
   - 2명 동의, 1명 반대: 중간~강한 값 (4-6 또는 1/4-1/6)
   - 의견 갈림: 보통 값 (2-4)
   - 완전 대립: 중립 값 (1-1.5)

3. **반드시 0.5 단위 사용**: 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9

4. **점수 다양성 필수**: 
   - 같은 점수를 3번 이상 사용하지 마세요!
   - 10개 쌍은 최대한 다른 점수를 받아야 합니다
   - 예: 3.5가 4개면 안됩니다. 2.5, 3.0, 3.5, 4.0으로 분산하세요
   - 각 쌍의 고유한 특성을 반영하여 차별화된 점수를 부여하세요

5. **점수 범위 적극 활용**: 
   - 1-9 전체 척도를 활용하세요
   - Agent들이 강하게 합의한 경우 6-8 범위 적극 사용
   - 의견이 갈릴 때만 2-4 범위 사용
   - 중립적일 때만 1-2 사용
   - 9는 거의 비교 불가능한 경우만 사용하세요"""

    user_prompt = f"""
12턴의 토론:
{debate_summary}

각 Agent의 제안:
{proposals_text}

다음 {len(pairs)}개 쌍의 최종 비교값을 결정하세요:
{pairs_text}

**각 점수의 의미를 정확히 이해하고, 토론 내용을 반영하여 균형잡힌 값을 사용하세요.**

**점수 가이드 (0.5 단위):**
- 1: 거의 동등
- 1.5-2: 아주 약간/조금 더 중요
- 2.5-3: 약간/분명히 더 중요
- 3.5-4: 상당히/매우 중요
- 4.5-5: 훨씬/강하게 더 중요
- 5.5-6: 매우 강하게/지배적으로 중요
- 6.5-7: 극도로/절대적으로 중요
- 7.5-9: 최고 수준/압도적 우위 (드물게 사용)

**필수: 넓은 점수 범위 사용하기**
- 1-9 전체 척도를 골고루 활용하세요
- 모든 점수가 비슷한 범위(예: 2-4)에만 몰려있으면 안 됩니다
- 토론에서 강한 합의가 있었다면 5.0 이상의 높은 점수를 적극 사용하세요
- 의견이 비슷하거나 대립한다면 낮은 점수(1.0-2.0)도 사용하세요
- 각 쌍의 중요도 차이를 점수 범위로 명확히 구분하세요

**토론 내용을 점수로 변환:**
- Agent 3명 모두 동의 → **6-8** 사용
- Agent 2명 강하게 동의 → **4-6** 사용
- Agent 2명 약하게 동의 → **3-4** 사용
- 의견이 갈림 → **2-3** 사용
- Agent 2명이 반대 → **1-2** 사용 (역수 사용)

**구체적 예시:**
- "A가 절대적으로 중요하다" (3명 합의) → 7.0
- "A가 훨씬 중요하다" (2명 합의) → 5.0
- "A가 약간 중요하다" (의견 갈림) → 2.5
- "거의 비슷하다" (완전 대립) → 1.0

역수 예시: 1/2=0.5, 1/3=0.33, 1/4=0.25, 1/5=0.2, 1/6=0.17, 1/7=0.14

JSON 형식으로 답변:
```json
{{"comparison_matrix": {{"기준A vs 기준B": 숫자, ...}}, "reasoning": "각 점수 결정 이유 설명"}}
```
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
        print(f"JSON 파싱 실패: {e}")
        decision_data = {}
    
    return {
        "turn": len(debate_history) + 1,
        "phase": "Phase 4: Director 최종 결정",
        "speaker": "Director",
        "type": "final_decision",
        "content": content,
        "comparison_matrix": decision_data.get('comparison_matrix', {}),
        "reasoning": decision_data.get('reasoning', ''),
        "timestamp": datetime.now().isoformat()
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

