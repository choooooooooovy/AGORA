"""Output schema definitions"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CriterionDetail(BaseModel):
    """Detailed information about a criterion"""
    name: str
    description: str
    type: str  # 'benefit' or 'cost'
    weight: float
    proposed_by: List[str]  # List of agents who proposed this


class AHPDetail(BaseModel):
    """AHP calculation details"""
    criteria_weights: Dict[str, float]
    consistency_ratio: float
    eigenvalue_max: float
    retry_count: int
    status: str  # 'passed' or 'failed'


class MajorScore(BaseModel):
    """Score details for a major"""
    major: str
    rank: int
    closeness_coefficient: float
    criterion_scores: Dict[str, float]  # Raw scores
    weighted_scores: Dict[str, float]  # Weighted scores
    distance_to_ideal: float
    distance_to_anti_ideal: float


class SessionOutput(BaseModel):
    """Complete session output"""
    session_id: str
    timestamp: str
    status: str  # 'success', 'partial', 'failed'
    
    # Input summary
    user_weights: Dict[str, int]
    alternatives: List[str]
    
    # Round 1 results
    criteria: List[CriterionDetail]
    
    # Round 2 results
    ahp_details: AHPDetail
    
    # Round 3 results
    decision_matrix: Dict[str, Dict[str, float]]  # {major: {criterion: score}}
    
    # Round 4 results
    final_ranking: List[MajorScore]
    
    # Metadata
    total_conversation_turns: int
    execution_time_seconds: Optional[float]
    errors: List[str]
    warnings: List[str]
