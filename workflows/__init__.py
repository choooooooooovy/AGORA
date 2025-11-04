"""Workflow modules - 간소화된 버전"""

from .round1_criteria import run_round1_debate
from .round2_ahp import run_round2_debate
from .round3_scoring import run_round3_debate
from .round4_topsis import calculate_topsis_ranking

__all__ = [
    'run_round1_debate',
    'run_round2_debate',
    'run_round3_debate',
    'calculate_topsis_ranking'
]
