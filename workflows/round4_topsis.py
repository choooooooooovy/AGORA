"""Round 4: TOPSIS 최종 순위 계산"""

from typing import Dict, Any


def calculate_topsis_ranking(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    TOPSIS 방법으로 최종 순위 계산
    
    Args:
        state: ConversationState
        
    Returns:
        업데이트된 state
    """
    from utils import TOPSISCalculator
    
    # 필요한 데이터 추출 (alternatives는 user_input에서)
    alternatives = state.get('user_input', {}).get('candidate_majors', [])
    selected_criteria = state.get('selected_criteria', [])
    criteria_names = [c['name'] for c in selected_criteria]
    decision_matrix = state.get('decision_matrix', {})
    criteria_weights = state.get('criteria_weights', {})
    
    # criterion_types 제거: 모든 기준은 benefit type (높을수록 좋음)
    
    # TOPSIS 계산
    topsis = TOPSISCalculator()
    
    try:
        topsis_result = topsis.process_topsis(
            alternatives=alternatives,
            criteria=criteria_names,
            scores=decision_matrix,
            weights=criteria_weights
            # criterion_types 제거
        )
        
        # State에 결과 저장
        state['topsis_result'] = topsis_result
        state['final_ranking'] = topsis_result.get('ranking', [])
        state['status'] = 'success'
        
    except Exception as e:
        state['status'] = 'failed'
        state['errors'] = state.get('errors', []) + [str(e)]
    
    return state


def format_final_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 출력 형식화
    
    Args:
        state: ConversationState
        
    Returns:
        SessionOutput 형태의 딕셔너리
    """
    import time
    from datetime import datetime
    
    # 기본 정보
    output = {
        'session_id': state.get('session_id', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'status': state.get('status', 'unknown'),
        
        # 입력 요약 (alternatives 제거, user_input.candidate_majors 사용)
        'user_weights': state['user_input'].get('agent_config', {}),
        
        # Round 1 결과
        'criteria': state.get('selected_criteria', []),
        
        # Round 2 결과
        'ahp_details': {
            'criteria_weights': state.get('criteria_weights', {}),
            'consistency_ratio': state.get('ahp_result', {}).get('cr', 0.0),
            'eigenvalue_max': state.get('ahp_result', {}).get('lambda_max', 0.0),
            'retry_count': state.get('ahp_result', {}).get('retry_count', 0),
            'status': state.get('ahp_result', {}).get('status', 'unknown')
        },
        
        # Round 3 결과
        'decision_matrix': state.get('decision_matrix', {}),
        
        # Round 4 결과
        'final_ranking': state.get('final_ranking', []),
        
        # 메타데이터
        'total_conversation_turns': state.get('conversation_turns', 0),
        'execution_time_seconds': state.get('execution_time', 0.0),
        'errors': state.get('errors', []),
        'warnings': state.get('warnings', [])
    }
    
    return output


def generate_summary_report(state: Dict[str, Any]) -> str:
    """
    결과 요약 보고서 생성
    
    Args:
        state: ConversationState
        
    Returns:
        마크다운 형식의 요약 보고서
    """
    report_lines = [
        "# 전공 우선순위 분석 결과",
        "",
        "## 최종 순위",
        ""
    ]
    
    # 순위 테이블
    for rank_info in state.get('final_ranking', []):
        rank = rank_info['rank']
        major = rank_info['major']
        closeness = rank_info['closeness_coefficient']
        report_lines.append(f"{rank}. **{major}** (근접도: {closeness:.4f})")
    
    report_lines.extend([
        "",
        "## 평가 기준 가중치",
        ""
    ])
    
    # 기준 가중치
    for criterion, weight in state.get('criteria_weights', {}).items():
        report_lines.append(f"- {criterion}: {weight:.4f} ({weight*100:.2f}%)")
    
    report_lines.extend([
        "",
        "## 통계",
        "",
        f"- 총 대화 턴: {state.get('conversation_turns', 0)}",
        f"- 실행 시간: {state.get('execution_time', 0.0):.2f}초",
        f"- 일관성 비율(CR): {state.get('ahp_result', {}).get('cr', 0.0):.4f}",
        ""
    ])
    
    return "\n".join(report_lines)
