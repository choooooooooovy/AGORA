"""Round 2: 쌍대비교 및 AHP 가중치 계산"""

import yaml
from typing import Dict, Any, List, Tuple
from pathlib import Path
from itertools import combinations


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_comparison_pairs(criteria: List[str]) -> List[Tuple[str, str]]:
    """
    쌍대비교할 기준 쌍 생성
    
    Args:
        criteria: 기준 리스트
        
    Returns:
        비교 쌍 리스트 [(A, B), (A, C), (B, C), ...]
    """
    return list(combinations(criteria, 2))


def agent_compare_criteria(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 에이전트가 순차적으로 대화하며 현재 비교 쌍에 대해 의견 제시
    
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
    round2_prompts = prompts['round2_ahp_pairwise']
    
    # 현재 비교 쌍
    current_pair = state.get('current_comparison_pair')
    if current_pair is None:
        return state
    
    criterion_a, criterion_b = current_pair
    
    # 사용자 맥락 준비
    user_context_data = state['user_input'].get('context', {})
    user_context = f"""
- 성격: {user_context_data.get('personality', 'N/A')}
- 학습 스타일: {user_context_data.get('learning_style', 'N/A')}
- 선호 과목: {', '.join(user_context_data.get('preferred_subjects', []))}
- 능력: {user_context_data.get('self_ability', {})}
"""
    
    # 확정된 기준 목록
    criteria_list = '\n'.join([f"- {c}" for c in state.get('selected_criteria', [])])
    
    # 공통 질문 생성
    base_question = round2_prompts['director_question'].format(
        criteria_list=criteria_list,
        criterion_a=criterion_a,
        criterion_b=criterion_b,
        user_context=user_context
    )
    
    # Context 준비
    context = {
        'personality': user_context_data.get('personality'),
        'learning_style': user_context_data.get('learning_style'),
        'preferred_subjects': user_context_data.get('preferred_subjects', []),
        'self_ability': user_context_data.get('self_ability', {}),
        'alternatives': state['alternatives'],
        'selected_criteria': state.get('selected_criteria', [])
    }
    
    # 에이전트 순서 정의 (가중치 낮은 순 → 높은 순)
    agent_config = state['user_input'].get('agent_config', {})
    agent_order = [
        ('ValueAgent', state.get('value_agent'), agent_config.get('value_weight', 0)),
        ('FitAgent', state.get('fit_agent'), agent_config.get('fit_weight', 0)),
        ('MarketAgent', state.get('market_agent'), agent_config.get('market_weight', 0))
    ]
    # 가중치 낮은 순으로 정렬 (가중치 낮은 사람이 먼저 발언)
    agent_order.sort(key=lambda x: x[2])
    
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
            round_type='comparison'
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
    
    # State에 현재 쌍의 대화 저장
    if 'round2_comparisons' not in state:
        state['round2_comparisons'] = {}
    
    state['round2_comparisons'][current_pair] = conversation
    state['conversation_turns'] += len(conversation)
    
    return state


def director_consensus_comparison(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    DirectorAgent가 대화를 종합하여 최종 비교값 합의
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from agents import DirectorAgent
    from utils.conversation_builder import build_director_consensus_prompt
    from datetime import datetime
    import re
    
    # 현재 비교 쌍
    current_pair = state.get('current_comparison_pair')
    if current_pair is None:
        return state
    
    criterion_a, criterion_b = current_pair
    
    # 현재 쌍에 대한 대화 가져오기
    conversation = state.get('round2_comparisons', {}).get(current_pair, [])
    
    if not conversation:
        return state
    
    # DirectorAgent
    director = state.get('director_agent')
    if director is None:
        raise ValueError("DirectorAgent not initialized")
    
    # Director용 프롬프트 생성
    question_context = f'"{criterion_a}"와 "{criterion_b}" 중 어느 기준이 더 중요한가?'
    director_prompt = build_director_consensus_prompt(
        conversation=conversation,
        question_context=question_context,
        round_type='comparison'
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
    
    # 응답에서 최종 비교값 추출
    final_value = extract_comparison_value(director_response)
    
    # DirectorDecision 생성
    director_decision = {
        'turn': len(conversation) + 1,
        'agent_name': 'DirectorAgent',
        'response': director_response,
        'final_value': final_value,
        'criterion_pair': current_pair,
        'timestamp': datetime.now().isoformat()
    }
    
    # 대화에 Director 응답 추가
    conversation.append(director_decision)
    state['round2_comparisons'][current_pair] = conversation
    
    # 별도로 Director 결정 저장 (검색 용이)
    if 'round2_director_decisions' not in state:
        state['round2_director_decisions'] = {}
    state['round2_director_decisions'][current_pair] = director_decision
    
    # 비교 행렬에 최종값 저장
    if 'comparison_matrix' not in state:
        state['comparison_matrix'] = {}
    state['comparison_matrix'][current_pair] = final_value
    
    state['conversation_turns'] += 1
    
    return state


def extract_comparison_value(response: str) -> float:
    """
    DirectorAgent 응답에서 최종 비교값 추출
    
    Args:
        response: DirectorAgent의 응답 텍스트
        
    Returns:
        추출된 비교값 (float)
    """
    import re
    
    # 패턴 1: "최종 확정값: 2.5" 형태
    pattern1 = r'최종\s*확정값\s*[:：]\s*([0-9.]+)'
    match1 = re.search(pattern1, response, re.IGNORECASE)
    if match1:
        try:
            return float(match1.group(1))
        except:
            pass
    
    # 패턴 2: "최종값: 2.5" 형태
    pattern2 = r'최종값\s*[:：]\s*([0-9.]+)'
    match2 = re.search(pattern2, response, re.IGNORECASE)
    if match2:
        try:
            return float(match2.group(1))
        except:
            pass
    
    # 패턴 3: "비교값: 2.5" 형태
    pattern3 = r'비교값\s*[:：]\s*([0-9.]+)'
    match3 = re.search(pattern3, response, re.IGNORECASE)
    if match3:
        try:
            return float(match3.group(1))
        except:
            pass
    
    # 패턴 4: DirectorAgent의 extract_final_value 메서드 활용
    # (기존 로직과 호환)
    pattern4 = r'\[최종 확정값\]\s*[:\n]?\s*([^\n]+)'
    match4 = re.search(pattern4, response)
    if match4:
        value_str = match4.group(1).strip()
        try:
            # 한글 제거
            value_str = value_str.replace('점', '').replace('배', '').strip()
            # 분수 처리
            if '/' in value_str:
                parts = value_str.split('/')
                if len(parts) == 2:
                    return round(float(parts[0]) / float(parts[1]), 4)
            return float(value_str)
        except:
            pass
    
    # 기본값: 1.0 (동등)
    print(f"[WARNING] 비교값 추출 실패, 기본값 1.0 사용")
    return 1.0


def calculate_ahp_weights(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    AHP 계산으로 기준별 가중치 도출
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from utils import AHPCalculator
    
    # 선정된 기준들
    selected_criteria = state.get('selected_criteria', [])
    if not selected_criteria:
        raise ValueError("No criteria selected")
    
    # selected_criteria가 딕셔너리 리스트인지 문자열 리스트인지 확인
    if selected_criteria and isinstance(selected_criteria[0], dict):
        criteria_names = [c['name'] for c in selected_criteria]
    else:
        # 문자열 리스트인 경우 그대로 사용
        criteria_names = selected_criteria
    
    # 쌍대비교 결과 수집
    comparisons = {}
    for pair, decision in state.get('round2_director_decisions', {}).items():
        # decision은 이제 전체 대화 객체
        value = decision.get('final_value')
        if isinstance(value, (int, float)):
            comparisons[pair] = float(value)
    
    # AHP 계산
    ahp = AHPCalculator(max_cr=0.10, max_retries=3)
    
    max_retries = 3
    retry_count = 0
    ahp_result = None
    
    while retry_count < max_retries:
        ahp_result = ahp.process_ahp(criteria_names, comparisons)
        
        if ahp_result['status'] == 'passed':
            break
        
        retry_count += 1
        # TODO: CR이 높으면 에이전트에게 재비교 요청
        # 현재는 단순히 재시도
    
    # State에 AHP 결과 저장
    state['ahp_result'] = ahp_result
    state['criteria_weights'] = ahp_result.get('weights', {})
    
    return state


def should_continue_comparisons(state: Dict[str, Any]) -> str:
    """
    쌍대비교를 계속할지 결정 (LangGraph 조건부 엣지용)
    
    Args:
        state: ConversationState
        
    Returns:
        'continue' 또는 'finish'
    """
    selected_criteria = state.get('selected_criteria', [])
    criteria_names = [c['name'] for c in selected_criteria]
    
    # 모든 비교 쌍 생성
    all_pairs = generate_comparison_pairs(criteria_names)
    
    # 완료된 비교 쌍
    completed_pairs = set(state.get('round2_director_decisions', {}).keys())
    
    # 남은 쌍이 있는지 확인
    remaining_pairs = [p for p in all_pairs if p not in completed_pairs]
    
    if remaining_pairs:
        # 다음 비교 쌍 설정
        state['current_comparison_pair'] = remaining_pairs[0]
        return 'continue'
    else:
        state['current_comparison_pair'] = None
        return 'finish'
