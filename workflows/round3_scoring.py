"""Round 3: 전공별 점수 부여"""

import yaml
from typing import Dict, Any, List
from pathlib import Path


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def agent_score_alternative(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 에이전트가 순차적으로 대화하며 (전공, 기준) 조합에 대해 점수 부여
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from agents import ValueAgent, FitAgent, MarketAgent
    from utils.conversation_builder import build_discussion_prompt
    from datetime import datetime
    
    # 프롬프트 로드
    prompts = load_prompts()
    round3_prompts = prompts['round3_scoring']
    
    # 현재 평가 항목
    current_item = state.get('current_scoring_item')
    if current_item is None:
        return state
    
    major, criterion = current_item
    
    # 에이전트 순서 정의 (가중치 낮은 순 → 높은 순)
    agent_config = state['user_input'].get('agent_config', {})
    agent_order = [
        ('ValueAgent', state.get('value_agent'), agent_config.get('value_weight', 0)),
        ('FitAgent', state.get('fit_agent'), agent_config.get('fit_weight', 0)),
        ('MarketAgent', state.get('market_agent'), agent_config.get('market_weight', 0))
    ]
    agent_order.sort(key=lambda x: x[2])
    
    # 기준 정보 가져오기
    criterion_info = {}
    selected_criteria = state.get('selected_criteria', [])
    if selected_criteria and isinstance(selected_criteria[0], dict):
        criterion_info = next(
            (c for c in selected_criteria if c.get('name') == criterion),
            {}
        )
    
    # 기본 질문 생성
    base_question = f"""
다음 전공을 "{criterion}" 기준으로 평가하세요:

**전공**: {major}
**평가 기준**: {criterion}
**기준 설명**: {criterion_info.get('description', '(설명 없음)')}

0-9점 사이로 점수를 부여하고, 반드시 근거를 포함하세요.
"""
    
    # Context 준비
    context = {
        'personality': state['user_input'].get('context', {}).get('personality'),
        'abilities': state['user_input'].get('context', {}).get('self_ability'),
        'preferences': state['user_input'].get('context', {}).get('preferred_subjects'),
        'alternatives': state['alternatives'],
        'selected_criteria': state.get('selected_criteria', [])
    }
    
    # 순차적 대화 진행
    conversation = []
    
    for idx, (agent_name, agent, weight) in enumerate(agent_order):
        if agent is None:
            continue
        
        # 대화 히스토리를 포함한 프롬프트 생성
        prompt = build_discussion_prompt(
            base_question=base_question,
            previous_responses=conversation,
            current_agent=agent_name,
            round_type='scoring'
        )
        
        # 에이전트 응답 생성
        response = agent.respond(context, prompt)
        
        # 대화에 추가
        conversation.append({
            'turn': idx + 1,
            'agent_name': agent_name,
            'agent_weight': weight,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    # State에 현재 항목의 대화 저장
    if 'round3_scores' not in state:
        state['round3_scores'] = {}
    
    state['round3_scores'][current_item] = conversation
    state['conversation_turns'] += len(conversation)
    
    return state


def director_consensus_score(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    DirectorAgent가 대화를 종합하여 최종 점수 합의
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from agents import DirectorAgent
    from utils.conversation_builder import build_director_consensus_prompt
    from datetime import datetime
    import re
    
    # 현재 평가 항목
    current_item = state.get('current_scoring_item')
    if current_item is None:
        return state
    
    major, criterion = current_item
    
    # 현재 항목에 대한 대화 가져오기
    conversation = state.get('round3_scores', {}).get(current_item, [])
    
    if not conversation:
        return state
    
    # DirectorAgent
    director = state.get('director_agent')
    if director is None:
        raise ValueError("DirectorAgent not initialized")
    
    # Director용 프롬프트 생성
    question_context = f'"{major}"를 "{criterion}" 기준으로 평가한 최종 점수 (0-9점)'
    director_prompt = build_director_consensus_prompt(
        conversation=conversation,
        question_context=question_context,
        round_type='scoring'
    )
    
    # Context 준비
    context = {
        'agent_config': state['user_input'].get('agent_config', {}),
        'alternatives': state['alternatives']
    }
    
    # DirectorAgent 응답 생성
    director_response = director.respond(
        context=context,
        round_prompt=director_prompt,
        agent_responses=conversation
    )
    
    # 응답에서 최종 점수 추출
    final_score = extract_score_value(director_response)
    
    # DirectorDecision 생성
    director_decision = {
        'turn': len(conversation) + 1,
        'agent_name': 'DirectorAgent',
        'response': director_response,
        'final_score': final_score,
        'major': major,
        'criterion': criterion,
        'timestamp': datetime.now().isoformat()
    }
    
    # 대화에 Director 응답 추가
    conversation.append(director_decision)
    state['round3_scores'][current_item] = conversation
    
    # 별도로 Director 결정 저장
    if 'round3_director_decisions' not in state:
        state['round3_director_decisions'] = {}
    state['round3_director_decisions'][current_item] = director_decision
    
    # 의사결정 행렬에 최종 점수 저장
    if 'decision_matrix' not in state:
        state['decision_matrix'] = {}
    if major not in state['decision_matrix']:
        state['decision_matrix'][major] = {}
    state['decision_matrix'][major][criterion] = final_score
    
    state['conversation_turns'] += 1
    
    return state


def extract_score_value(response: str) -> float:
    """
    DirectorAgent 응답에서 최종 점수 추출
    
    Args:
        response: DirectorAgent의 응답 텍스트
        
    Returns:
        추출된 점수 (0-9 사이의 float)
    """
    import re
    
    # 패턴 1: "최종 점수: 7.5점" 형태
    pattern1 = r'최종\s*점수\s*[:：]\s*([0-9.]+)\s*점?'
    match1 = re.search(pattern1, response, re.IGNORECASE)
    if match1:
        try:
            score = float(match1.group(1))
            return max(0, min(9, score))  # 0-9 범위로 제한
        except:
            pass
    
    # 패턴 2: "점수: 7.5" 형태
    pattern2 = r'점수\s*[:：]\s*([0-9.]+)'
    match2 = re.search(pattern2, response, re.IGNORECASE)
    if match2:
        try:
            score = float(match2.group(1))
            return max(0, min(9, score))
        except:
            pass
    
    # 패턴 3: "[최종 점수]" 섹션
    pattern3 = r'\[최종\s*점수\]\s*[:\n]?\s*([0-9.]+)'
    match3 = re.search(pattern3, response, re.IGNORECASE)
    if match3:
        try:
            score = float(match3.group(1))
            return max(0, min(9, score))
        except:
            pass
    
    # 기본값: 5.0 (중간값)
    print(f"[WARNING] 점수 추출 실패, 기본값 5.0 사용")
    return 5.0
    
    # 기준 정보
    criterion_info = next(
        (c for c in state.get('selected_criteria', []) if c['name'] == criterion),
        {}
    )
    
    # 프롬프트 변수 주입
    agent_config = state['user_input'].get('agent_config', {})
    formatted_prompt = director_prompt.format(
        major=major,
        criterion=criterion,
        criterion_description=criterion_info.get('description', ''),
        agent_responses=formatted_responses,
        value_weight=agent_config.get('value_weight', 0),
        fit_weight=agent_config.get('fit_weight', 0),
        market_weight=agent_config.get('market_weight', 0)
    )
    
    # Context 준비
    context = {
        'agent_config': agent_config
    }
    
    # DirectorAgent 응답 생성
    response = director.respond(
        context=context,
        round_prompt=formatted_prompt,
        agent_responses=agent_responses
    )
    
    # 최종 점수 추출
    final_score = director.extract_final_value(response)
    
    # State에 결과 저장
    if 'round3_director_decisions' not in state:
        state['round3_director_decisions'] = {}
    
    state['round3_director_decisions'][current_item] = {
        'response': response,
        'score': final_score
    }
    
    state['conversation_turns'] += 1
    
    return state


def build_decision_matrix(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    의사결정 행렬 구성
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    alternatives = state.get('alternatives', [])
    selected_criteria = state.get('selected_criteria', [])
    criteria_names = [c['name'] for c in selected_criteria]
    
    # 의사결정 행렬 초기화
    decision_matrix = {}
    
    for major in alternatives:
        decision_matrix[major] = {}
        for criterion in criteria_names:
            # 해당 (전공, 기준) 조합의 점수 가져오기
            item = (major, criterion)
            decision = state.get('round3_director_decisions', {}).get(item, {})
            score = decision.get('score', 0.0)
            
            # float로 변환
            if isinstance(score, (int, float)):
                decision_matrix[major][criterion] = float(score)
            else:
                decision_matrix[major][criterion] = 0.0
    
    state['decision_matrix'] = decision_matrix
    
    return state


def should_continue_scoring(state: Dict[str, Any]) -> str:
    """
    점수 부여를 계속할지 결정 (LangGraph 조건부 엣지용)
    
    Args:
        state: ConversationState
        
    Returns:
        'continue' 또는 'finish'
    """
    alternatives = state.get('alternatives', [])
    selected_criteria = state.get('selected_criteria', [])
    criteria_names = [c['name'] for c in selected_criteria]
    
    # 모든 (전공, 기준) 조합 생성
    all_items = [(major, criterion) for major in alternatives for criterion in criteria_names]
    
    # 완료된 항목
    completed_items = set(state.get('round3_director_decisions', {}).keys())
    
    # 남은 항목이 있는지 확인
    remaining_items = [item for item in all_items if item not in completed_items]
    
    if remaining_items:
        # 다음 항목 설정
        state['current_scoring_item'] = remaining_items[0]
        return 'continue'
    else:
        state['current_scoring_item'] = None
        # 의사결정 행렬 구성
        build_decision_matrix(state)
        return 'finish'
