"""간소화된 워크플로우 엔진"""

import time
import uuid
from typing import Dict, Any, Optional


class WorkflowEngine:
    """간소화된 워크플로우 엔진 - 순차 실행만 수행"""
    
    def __init__(
        self,
        model_name: str = "gpt-4o",
        agent_temperature: float = 0.5,
        director_temperature: float = 0.0,
        max_criteria: int = 5
    ):
        """
        WorkflowEngine 초기화
        
        Args:
            model_name: OpenAI 모델 이름 (사용하지 않음, 호환성 유지)
            agent_temperature: 에이전트 온도 (사용하지 않음, 호환성 유지)
            director_temperature: Director 온도 (사용하지 않음, 호환성 유지)
            max_criteria: 최대 평가 기준 개수
        """
        self.max_criteria = max_criteria
    
    def initialize_state(
        self,
        user_input: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        초기 상태 생성
        
        Args:
            user_input: 사용자 입력
            session_id: 세션 ID (없으면 자동 생성)
            
        Returns:
            초기화된 state
        """
        from core.persona_generator import create_dynamic_personas
        
        print(f"\n[Workflow] 페르소나 생성 중...")
        agent_personas = create_dynamic_personas(user_input)
        print(f"[Workflow] {len(agent_personas)}개 페르소나 생성 완료!")
        for persona in agent_personas:
            print(f"  - {persona['name']}: {persona.get('perspective', 'N/A')}")
        
        # 초기 상태 구성
        state = {
            'session_id': session_id or str(uuid.uuid4()),
            'start_time': time.time(),
            'user_input': user_input,
            'agent_personas': agent_personas,
            'max_criteria': self.max_criteria,
            'conversation_turns': 0
        }
        
        return state
    
    def run_round1(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 1: 평가 기준 선정"""
        from workflows.round1_criteria import run_round1_debate
        return run_round1_debate(state)
    
    def run_round2(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 2: AHP 가중치 계산"""
        from workflows.round2_ahp import run_round2_debate
        return run_round2_debate(state)
    
    def run_round3(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 3: Decision Matrix 생성"""
        from workflows.round3_scoring import run_round3_debate
        return run_round3_debate(state)
    
    def run_round4(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 4: TOPSIS 최종 순위"""
        from workflows.round4_topsis import calculate_topsis_ranking
        return calculate_topsis_ranking(state)
