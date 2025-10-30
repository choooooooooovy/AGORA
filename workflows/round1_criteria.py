"""Round 1: 평가 기준 제안 및 선정"""

import yaml
from typing import Dict, Any
from pathlib import Path


def load_prompts() -> Dict[str, Any]:
    """프롬프트 YAML 파일 로드"""
    prompt_path = Path(__file__).parent.parent / "templates" / "round_prompts.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def agent_propose_criteria(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 에이전트가 순차적으로 평가 기준 제안 (대화형)
    이전 에이전트들의 발언을 보고 반응
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from agents import ValueAgent, FitAgent, MarketAgent
    
    # 프롬프트 로드
    prompts = load_prompts()
    round1_prompts = prompts['round1_criteria_generation']
    
    # 이미 제안이 완료된 경우 스킵
    proposals = state.get('round1_proposals', [])
    if len(proposals) >= 3:
        return state
    
    # 에이전트 순서 정의
    agent_order = [
        ('ValueAgent', state.get('value_agent')),
        ('FitAgent', state.get('fit_agent')),
        ('MarketAgent', state.get('market_agent'))
    ]
    
    # 현재 턴의 에이전트 선택
    current_turn = len(proposals)
    agent_name, agent = agent_order[current_turn]
    
    if agent is None:
        return state
    
    # Context 준비
    user_context_data = state['user_input'].get('context', {})
    context = {
        'personality': user_context_data.get('personality'),
        'learning_style': user_context_data.get('learning_style'),
        'evaluation_style': user_context_data.get('evaluation_style'),
        'preferred_subjects': user_context_data.get('preferred_subjects', []),
        'disliked_subjects': user_context_data.get('disliked_subjects', []),
        'self_ability': user_context_data.get('self_ability', {}),
        'evidence': user_context_data.get('evidence', {}),
        'alternatives': state['alternatives']
    }
    
    user_context = f"""
- 성격: {context.get('personality', 'N/A')}
- 학습 스타일: {context.get('learning_style', 'N/A')}
- 평가 스타일: {context.get('evaluation_style', 'N/A')}
- 선호 과목: {', '.join(context.get('preferred_subjects', []))}
- 능력: {context.get('self_ability', {})}
"""
    
    majors_str = ', '.join(state['alternatives'])
    
    # 기본 질문 프롬프트
    base_question = round1_prompts['director_question'].format(
        user_context=user_context,
        majors=majors_str
    )
    
    # 대화 히스토리 추가 (이전 에이전트들의 발언)
    conversation_history = ""
    if proposals:
        conversation_history = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        conversation_history += "[이전 대화 내용]\n"
        conversation_history += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, prev_proposal in enumerate(proposals, 1):
            conversation_history += f"[Turn {i} - {prev_proposal['agent_name']}]\n"
            conversation_history += f"{prev_proposal['criteria']}\n\n"
        
        conversation_history += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 강제 대화형 프롬프트 (명시적 응답 요구)
        conversation_history += f"당신은 {agent_name}입니다. 위 동료들의 의견에 대한 응답으로 다음 형식을 **반드시** 따라 작성하세요:\n\n"
        conversation_history += "### 이전 의견에 대한 응답\n"
        conversation_history += "(동료들이 제안한 기준 중 동의하는 부분과 그 이유를 먼저 언급하세요)\n\n"
        conversation_history += "### 제 의견\n"
        conversation_history += "(당신의 전문 분야 관점에서 추가로 필요한 기준을 제안하거나, 동료 의견에 대한 보완/반박 의견을 제시하세요)\n\n"
        conversation_history += "**중요:** 반드시 위 동료들의 구체적인 제안을 언급하며 응답해야 합니다. 독립적인 발언만 하지 마세요.\n"
    
    # 최종 질문 (대화 히스토리 포함)
    final_question = base_question + conversation_history
    
    # 현재 에이전트 응답 생성
    response = agent.respond(context, final_question)
    
    # 제안 추가
    proposals.append({
        'agent_name': agent_name,
        'criteria': response
    })
    
    # State 업데이트
    state['round1_proposals'] = proposals
    state['conversation_turns'] += 1
    
    return state


def director_select_criteria(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    DirectorAgent가 최종 평가 기준 선정
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from agents import DirectorAgent
    from utils.conversation_builder import build_director_consensus_prompt
    from datetime import datetime
    
    # 프롬프트 로드
    prompts = load_prompts()
    director_prompt = prompts['round1_criteria_generation']['director_consensus']
    
    # DirectorAgent
    director = state.get('director_agent')
    if director is None:
        raise ValueError("DirectorAgent not initialized")
    
    # 모든 제안을 대화 형식으로 변환
    conversation = []
    for idx, proposal in enumerate(state['round1_proposals'], 1):
        conversation.append({
            'turn': idx,
            'agent_name': proposal['agent_name'],
            'response': proposal['criteria'],
            'timestamp': datetime.now().isoformat()
        })
    
    # Director용 프롬프트 생성
    question_context = f"최대 {state.get('max_criteria', 5)}개의 평가 기준 선정"
    director_full_prompt = build_director_consensus_prompt(
        conversation=conversation,
        question_context=question_context,
        round_type='criteria'
    )
    
    # 기존 프롬프트와 결합 (호환성 유지)
    max_criteria = state.get('max_criteria', 5)
    agent_config = state['user_input'].get('agent_config', {})
    
    all_proposals = "\n\n".join([
        f"[{p['agent_name']}]\n{p['criteria']}"
        for p in state['round1_proposals']
    ])
    
    formatted_prompt = director_prompt.format(
        all_proposals=all_proposals,
        max_criteria=max_criteria,
        value_weight=agent_config.get('value_weight', 0),
        fit_weight=agent_config.get('fit_weight', 0),
        market_weight=agent_config.get('market_weight', 0)
    )
    
    # Director 프롬프트 결합
    final_prompt = director_full_prompt + "\n\n" + formatted_prompt
    
    # Context 준비
    context = {
        'agent_config': agent_config,
        'alternatives': state['alternatives']
    }
    
    # DirectorAgent 응답 생성
    response = director.respond(
        context=context,
        round_prompt=final_prompt,
        agent_responses=state['round1_proposals']
    )
    
    print(f"\n[DEBUG] DirectorAgent 응답 길이: {len(response)}")
    print(f"[DEBUG] 응답 시작: {response[:200]}...")
    
    # 응답에서 기준 파싱
    selected_criteria = parse_criteria_from_response(response)
    
    # DirectorDecision 생성 (명확한 구조)
    director_decision = {
        'turn': len(conversation) + 1,
        'agent_name': 'DirectorAgent',
        'response': response,
        'selected_criteria': selected_criteria,
        'max_criteria': max_criteria,
        'timestamp': datetime.now().isoformat()
    }
    
    # State 업데이트 - 명확하게 저장
    state['selected_criteria'] = selected_criteria
    state['round1_director_decision'] = director_decision
    
    # 검증 로그
    print(f"[DEBUG] round1_director_decision 설정 완료")
    print(f"[DEBUG] response 길이: {len(director_decision.get('response', ''))}")
    print(f"[DEBUG] selected_criteria 개수: {len(selected_criteria)}")
    print(f"[DEBUG] state에 저장된 키들: {list(state.keys())}")
    
    state['conversation_turns'] += 1
    
    return state


def parse_criteria_from_response(response: str) -> list:
    """
    DirectorAgent 응답에서 선정된 기준 파싱
    
    Args:
        response: DirectorAgent의 응답 텍스트
        
    Returns:
        선정된 기준 리스트 (기준명만)
        ['취업 전망', '개인 적성', '급여 수준', ...]
    """
    import re
    
    criteria = []
    
    # 패턴 1: "1. [기준명] (유형: benefit/cost) - ..." 형식
    pattern1 = r'\d+\.\s*\[([^\]]+)\]\s*\(유형:\s*(benefit|cost)\)'
    matches1 = re.findall(pattern1, response, re.IGNORECASE)
    
    if matches1:
        for name, _ in matches1:
            criteria.append(name.strip())
        return criteria
    
    # 패턴 2: "1. 기준명 (benefit/cost): ..." 형식
    pattern2 = r'\d+\.\s*([^(]+?)\s*\((benefit|cost)\)'
    matches2 = re.findall(pattern2, response, re.IGNORECASE)
    
    if matches2:
        for name, _ in matches2:
            criteria.append(name.strip())
        return criteria
    
    # 패턴 3: 단순히 번호 매겨진 목록 "1. 기준명"
    pattern3 = r'\d+\.\s*([^\n:]+)'
    matches3 = re.findall(pattern3, response)
    
    if matches3:
        # 괄호나 콜론 전까지만 추출
        for match in matches3[:5]:  # 최대 5개
            name = match.split('(')[0].split(':')[0].strip()
            if name and len(name) < 50:  # 너무 긴 문장 제외
                criteria.append(name)
        return criteria
    
    return criteria
    
    return criteria
