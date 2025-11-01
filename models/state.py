"""LangGraph State definitions"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
import numpy as np
import pandas as pd

# 기준 제안
class CriteriaProposal(TypedDict):
    agent_name: str
    turn: int
    criterion_name: str
    criterion_description: str
    criterion_type: str  # 'benefit' or 'cost'
    reasoning: str

# 쌍대 비교
class PairwiseComparison(TypedDict):
    agent_name: str
    turn: int
    criterion_a: str
    criterion_b: str
    comparison_value: float  # 1-9 scale
    reasoning: str

# 에이전트 점수
class AgentScore(TypedDict):
    agent_name: str
    turn: int
    major: str
    criterion: str
    score: float  # 0-9 scale (decimal allowed)
    reasoning: str

# 디렉터 결정
class DirectorDecision(TypedDict):
    question: str  # Question posed to agents
    agent_responses: List[Dict[str, Any]]  # All agent responses
    statistical_summary: Dict[str, float]  # Statistics (mean, median, etc.)
    weighted_calculation: Dict[str, Any]  # Weighted average calculation details
    reasoning: str  # Director's reasoning for final decision
    final_value: Any  # Final decided value (float, str, or list)

# TOPSIS 결과
class TOPSISResult(TypedDict):
    major: str
    normalized_scores: Dict[str, float]
    weighted_scores: Dict[str, float]
    distance_to_ideal: float
    distance_to_anti_ideal: float
    closeness_coefficient: float
    rank: int

# 주요 대화 상태
class ConversationState(TypedDict):
    
    # Session info
    session_id: str
    start_time: float
    conversation_turns: int
    
    # User input (immutable)
    user_input: Dict[str, Any]
    alternatives: List[str]
    
    # Agent 페르소나 (동적 생성)
    agent_personas: Optional[List[Dict[str, Any]]]
    # Format: [
    #   {
    #     "name": "개인만족중심Agent",
    #     "core_values": ["적성 일치", "워라밸"],
    #     "persona_description": "...",
    #     "debate_stance": "...",
    #     "system_prompt": "..."
    #   },
    #   {...}, {...}
    # ]
    
    # Agent instances (기존 유지 - 추후 제거 예정)
    value_agent: Any
    fit_agent: Any
    market_agent: Any
    director_agent: Any
    
    # Configuration
    max_criteria: int
    
    # Agent configuration (deprecated - using user weights directly)
    agent_weights: Optional[Dict[str, float]]  # {"ValueAgent": 0.2, "FitAgent": 0.6, "MarketAgent": 0.2}
    turns_per_agent: Optional[int]  # Number of turns each agent gets (equal for all)
    speaking_order: Optional[List[str]]  # Round-robin order: ["ValueAgent", "FitAgent", "MarketAgent", ...]
    total_turns: Optional[int]  # Total speaking turns (turns_per_agent * 3)
    current_turn: Optional[int]  # Current turn index (0-based)
    
    # Workflow control
    current_round: Optional[int]  # 1, 2, 3, or 4
    workflow_status: Optional[str]  # 'in_progress', 'completed', 'failed'
    
    # Round 1: Criteria generation
    round1_proposals: List[Dict[str, Any]]  # All proposals from agents
    
    # Round 1 구조화 토론 (13-turn structure)
    round1_debate_turns: Optional[List[Dict[str, Any]]]
    # Format: [
    #   {
    #     "turn": 1,
    #     "phase": "Agent A 주도권",
    #     "speaker": "개인만족중심Agent",
    #     "type": "proposal",  # proposal / question / answer
    #     "target": None,      # question일 때만 target 지정
    #     "content": "...",
    #     "timestamp": "2025-10-30T..."
    #   },
    #   ...
    # ]
    
    selected_criteria: Optional[List[str]]  # Final selected criteria names
    round1_director_decision: Optional[Dict[str, Any]]  # DirectorAgent's final decision with full response
    criteria_details: Optional[List[Dict[str, str]]]  # Criteria with details
    criteria_proposals: Optional[List[CriteriaProposal]]  # All proposals from agents
    criteria_director_decision: Optional[DirectorDecision]  # Director's final criteria decision
    final_criteria: Optional[List[Dict[str, str]]]  # Final agreed criteria
    # Format: [{"name": "passion", "description": "...", "type": "benefit"}, ...]
    
    # Round 2: AHP pairwise comparison
    current_comparison_pair: Optional[tuple]  # Current pair being compared (criterion_a, criterion_b)
    comparison_pairs: Optional[List[tuple]]  # All pairs to compare
    round2_comparisons: Dict[str, Any]  # All comparisons
    round2_director_decisions: Dict[str, Any]  # Director decisions
    pairwise_comparisons: Optional[List[PairwiseComparison]]  # All comparisons from agents
    pairwise_director_decisions: Optional[List[DirectorDecision]]  # Director decisions for each pair
    integrated_ahp_matrix: Optional[np.ndarray]  # Integrated pairwise comparison matrix
    criteria_weights: Optional[Dict[str, float]]  # Final weights from AHP
    # Format: {"passion": 0.35, "income": 0.25, ...}
    eigenvalue_max: Optional[float]  # Maximum eigenvalue
    consistency_index: Optional[float]  # CI value
    consistency_ratio: Optional[float]  # CR value
    cr_retry_count: Optional[int]  # Number of CR retries
    cr_status: Optional[str]  # 'not_started', 'in_progress', 'passed', 'failed'
    
    # Round 3: Alternative scoring
    current_scoring_item: Optional[tuple]  # Current item being scored (major, criterion)
    scoring_items: Optional[List[tuple]]  # All items to score
    round3_scores: Dict[str, Any]  # All scores
    round3_director_decisions: Dict[str, Any]  # Director decisions
    decision_matrix: Optional[Dict[str, Dict[str, float]]]  # major -> {criterion: score}
    agent_scores: Optional[List[AgentScore]]  # All scores from agents
    scoring_director_decisions: Optional[List[DirectorDecision]]  # Director decisions for each major-criterion
    integrated_decision_matrix: Optional[pd.DataFrame]  # Integrated decision matrix
    # Format: DataFrame with majors as rows, criteria as columns
    
    # Round 4: TOPSIS
    normalized_matrix: Optional[pd.DataFrame]  # Normalized decision matrix
    weighted_matrix: Optional[pd.DataFrame]  # Weighted normalized matrix
    ideal_solution: Optional[Dict[str, float]]  # Ideal solution (A+)
    anti_ideal_solution: Optional[Dict[str, float]]  # Anti-ideal solution (A-)
    topsis_results: Optional[List[TOPSISResult]]  # TOPSIS results for all majors
    final_ranking: Optional[List[tuple]]  # Final ranking: [(major, score), ...]
    final_output: Optional[str]  # Formatted final output
    
    # Conversation history
    messages: Optional[Annotated[List, add_messages]]  # All conversation messages
    
    # Error handling
    errors: Optional[List[str]]  # List of errors encountered
    warnings: Optional[List[str]]  # List of warnings
