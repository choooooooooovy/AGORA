"""간소화된 State definitions - 실제 사용하는 필드만 유지"""

from typing import Dict, List, Any, Optional


# 주요 대화 상태 - 실제 사용하는 필드만 유지
class ConversationState(Dict[str, Any]):
    """
    워크플로우 상태
    
    필수 필드:
    - session_id: str
    - user_input: Dict[str, Any]
    - agent_personas: List[Dict[str, Any]]
    - max_criteria: int
    
    Round 1 필드:
    - round1_debate_turns: List[Dict[str, Any]]
    - selected_criteria: List[Dict[str, str]]
    - round1_director_decision: Dict[str, Any]
    
    Round 2 필드:
    - round2_debate_turns: List[Dict[str, Any]]
    - comparison_matrix: Dict[str, float]
    - criteria_weights: Dict[str, float]
    - consistency_ratio: float
    
    Round 3 필드:
    - round3_debate_turns: List[Dict[str, Any]]
    - decision_matrix: Dict[str, Dict[str, float]]
    
    Round 4 필드:
    - topsis_result: Dict[str, Any]
    - final_ranking: List[Dict[str, Any]]
    """
    pass
