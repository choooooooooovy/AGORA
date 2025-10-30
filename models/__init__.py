"""Data models and schemas for the prioritization framework"""

import json
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

from models.user_input_schema import UserInput, SessionSettings
from models.state import ConversationState, CriteriaProposal, PairwiseComparison, AgentScore, DirectorDecision, TOPSISResult


def load_user_input(filepath: str) -> Dict[str, Any]:
    """
    사용자 입력 JSON 파일 로드 및 검증
    
    Args:
        filepath: JSON 파일 경로
        
    Returns:
        검증된 사용자 입력 딕셔너리
        
    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        ValidationError: 입력 형식이 잘못된 경우
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Pydantic 검증
    try:
        user_input = UserInput(**data)
        # 검증된 데이터를 딕셔너리로 반환
        return user_input.model_dump()
    except ValidationError as e:
        print(f"[ERROR] 입력 데이터 검증 실패:")
        for error in e.errors():
            print(f"  - {error['loc']}: {error['msg']}")
        raise


def format_final_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 결과를 출력 형식으로 변환
    
    Args:
        state: 최종 상태
        
    Returns:
        출력 형식의 결과 딕셔너리
    """
    return {
        'session_id': state.get('session_id'),
        'timestamp': state.get('timestamp'),
        'user_input': state.get('user_input'),
        'selected_criteria': state.get('selected_criteria', []),
        'criteria_weights': state.get('criteria_weights', {}),
        'consistency_ratio': state.get('consistency_ratio'),
        'decision_matrix': state.get('decision_matrix', {}),
        'topsis_results': state.get('topsis_results', []),
        'final_ranking': state.get('final_ranking', []),
        'conversation_turns': state.get('conversation_turns', 0)
    }


__all__ = [
    "UserInput",
    "UserContext", 
    "AgentConfig",
    "SelfAbility",
    "Evidence",
    "AlternativeConfig",
    "SessionSettings",
    "ConversationState",
    "CriteriaProposal",
    "PairwiseComparison",
    "AgentScore",
    "DirectorDecision",
    "TOPSISResult",
    "load_user_input",
    "format_final_output",
]

