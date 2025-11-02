"""워크플로우 엔진: LangGraph StateGraph 구성 및 실행"""

import time
import uuid
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from models.state import ConversationState
from workflows import (
    agent_propose_criteria,
    director_select_criteria,
    agent_compare_criteria,
    director_consensus_comparison,
    calculate_ahp_weights,
    run_round3_debate,
    agent_score_alternative,
    director_final_scoring,
    calculate_topsis_ranking
)
from workflows.round2_ahp import should_continue_comparisons, generate_comparison_pairs


class WorkflowEngine:
    """LangGraph 워크플로우 엔진"""
    
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
            model_name: OpenAI 모델 이름
            agent_temperature: 전문가 에이전트 온도
            director_temperature: DirectorAgent 온도
            max_criteria: 최대 평가 기준 개수
        """
        self.model_name = model_name
        self.agent_temperature = agent_temperature
        self.director_temperature = director_temperature
        self.max_criteria = max_criteria
        
        # StateGraph 생성
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        LangGraph StateGraph 구성
        
        Returns:
            구성된 StateGraph
        """
        # StateGraph 생성 (ConversationState 타입 사용)
        workflow = StateGraph(ConversationState)
        
        # ========== Round 1: 평가 기준 제안 및 선정 ==========
        workflow.add_node("propose_criteria", agent_propose_criteria)
        workflow.add_node("select_criteria", director_select_criteria)
        
        # ========== Round 2: 쌍대비교 및 AHP ==========
        workflow.add_node("compare_criteria", self._compare_criteria_wrapper)
        workflow.add_node("consensus_comparison", director_consensus_comparison)
        workflow.add_node("calculate_ahp", calculate_ahp_weights)
        
        # ========== Round 3: 점수 부여 ==========
        workflow.add_node("score_alternative", self._score_alternative_wrapper)
        workflow.add_node("consensus_score", director_final_scoring)
        
        # ========== Round 4: TOPSIS 순위 ==========
        workflow.add_node("calculate_ranking", calculate_topsis_ranking)
        
        # ========== 엣지 연결 ==========
        
        # 시작 → Round 1
        workflow.set_entry_point("propose_criteria")
        workflow.add_edge("propose_criteria", "select_criteria")
        
        # Round 1 → Round 2 (첫 번째 비교 쌍 설정)
        workflow.add_edge("select_criteria", "compare_criteria")
        
        # Round 2 루프
        workflow.add_edge("compare_criteria", "consensus_comparison")
        workflow.add_conditional_edges(
            "consensus_comparison",
            should_continue_comparisons,
            {
                "continue": "compare_criteria",  # 다음 쌍 비교
                "finish": "calculate_ahp"        # AHP 계산
            }
        )
        
        # Round 2 → Round 3 (첫 번째 점수 항목 설정)
        workflow.add_edge("calculate_ahp", "score_alternative")
        
        # Round 3: 한 번에 전체 Decision Matrix 생성
        workflow.add_edge("score_alternative", "consensus_score")
        workflow.add_edge("consensus_score", "calculate_ranking")
        
        # Round 4 → 종료
        workflow.add_edge("calculate_ranking", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    def _compare_criteria_wrapper(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        쌍대비교 래퍼 (첫 번째 쌍 설정 포함)
        
        Args:
            state: ConversationState
            
        Returns:
            업데이트된 state
        """
        # 첫 번째 호출 시 비교 쌍 초기화
        if 'current_comparison_pair' not in state or state.get('current_comparison_pair') is None:
            selected_criteria = state.get('selected_criteria', [])
            
            # selected_criteria가 문자열 리스트인 경우 (기준명만)
            if selected_criteria and isinstance(selected_criteria[0], str):
                criteria_names = selected_criteria
            # selected_criteria가 딕셔너리 리스트인 경우
            else:
                criteria_names = [c['name'] for c in selected_criteria]
            
            all_pairs = generate_comparison_pairs(criteria_names)
            
            if all_pairs:
                state['current_comparison_pair'] = all_pairs[0]
            else:
                # 기준이 1개 이하면 비교 불필요
                state['current_comparison_pair'] = None
                return state
        
        # 실제 비교 수행
        return agent_compare_criteria(state)
    
    def _score_alternative_wrapper(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        점수 부여 래퍼 (첫 번째 항목 설정 포함)
        
        Args:
            state: ConversationState
            
        Returns:
            업데이트된 state
        """
        # 첫 번째 호출 시 점수 항목 초기화
        if 'current_scoring_item' not in state or state.get('current_scoring_item') is None:
            alternatives = state.get('alternatives', [])
            selected_criteria = state.get('selected_criteria', [])
            
            # selected_criteria가 문자열 리스트인 경우
            if selected_criteria and isinstance(selected_criteria[0], str):
                criteria_names = selected_criteria
            # selected_criteria가 딕셔너리 리스트인 경우
            else:
                criteria_names = [c['name'] for c in selected_criteria]
            
            all_items = [(major, criterion) for major in alternatives for criterion in criteria_names]
            
            if all_items:
                state['current_scoring_item'] = all_items[0]
            else:
                state['current_scoring_item'] = None
                return state
        
        # 실제 점수 부여 수행
        return agent_score_alternative(state)
    
    def initialize_state(
        self,
        user_input: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        초기 상태 생성
        
        Args:
            user_input: 사용자 입력 (UserInput 딕셔너리)
            session_id: 세션 ID (없으면 자동 생성)
            
        Returns:
            초기화된 ConversationState
        """
        # 동적 페르소나 생성
        from core.persona_generator import create_dynamic_personas
        
        print(f"\n[Workflow] 페르소나 생성 중...")
        agent_personas = create_dynamic_personas(user_input)
        print(f"[Workflow] {len(agent_personas)}개 페르소나 생성 완료!")
        for persona in agent_personas:
            print(f"  - {persona['name']}: {', '.join(persona['core_values'])}")
        
        # 초기 상태 구성
        state = {
            # 세션 정보
            'session_id': session_id or str(uuid.uuid4()),
            'start_time': time.time(),
            
            # 사용자 입력
            'user_input': user_input,
            'alternatives': user_input.get('candidate_majors', user_input.get('alternatives', [])),
            
            # 동적 생성된 페르소나
            'agent_personas': agent_personas,
            
            # 설정
            'max_criteria': self.max_criteria,
            
            # 진행 상황 추적
            'conversation_turns': 0,
            'current_comparison_pair': None,
            'current_scoring_item': None,
            
            # 결과 저장소 초기화
            'round1_proposals': [],
            'round1_debate_turns': None,  # 토론 시스템 결과 저장
            'round2_comparisons': {},
            'round2_director_decisions': {},
            'round3_scores': {},
            'round3_director_decisions': {},
            
            # 에러/경고
            'errors': [],
            'warnings': []
        }
        
        return state
    
    def run(
        self,
        user_input: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 워크플로우 실행
        
        Args:
            user_input: 사용자 입력
            session_id: 세션 ID
            
        Returns:
            최종 결과 상태
        """
        # 초기 상태 생성
        initial_state = self.initialize_state(user_input, session_id)
        
        # 그래프 실행
        final_state = self.graph.invoke(initial_state)
        
        # 실행 시간 계산
        final_state['execution_time'] = time.time() - final_state['start_time']
        
        return final_state
    
    def run_stream(
        self,
        user_input: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """
        워크플로우를 스트리밍 모드로 실행 (진행 상황 실시간 확인)
        
        Args:
            user_input: 사용자 입력
            session_id: 세션 ID
            
        Yields:
            각 노드 실행 후의 상태
        """
        # 초기 상태 생성
        initial_state = self.initialize_state(user_input, session_id)
        
        # 그래프 스트리밍 실행
        for state_update in self.graph.stream(initial_state):
            yield state_update
    
    # ========== 라운드별 실행 메서드 ==========
    
    def run_round1(
        self,
        user_input: Dict[str, Any],
        streaming: bool = False,
        callback = None
    ) -> Dict[str, Any]:
        """
        Round 1: 평가 기준 제안 및 선정
        
        Args:
            user_input: 사용자 입력
            streaming: 스트리밍 모드 사용 여부
            callback: 진행 상황 콜백 함수 (streaming=True일 때 사용)
            
        Returns:
            Round 1 완료 상태
        """
        # Round 1만을 위한 그래프 생성 (순차적 대화)
        def should_continue_proposals(state: Dict[str, Any]) -> str:
            """3명의 제안이 모두 완료되었는지 확인"""
            proposals = state.get('round1_proposals', [])
            if len(proposals) >= 3:
                return "finish"
            return "continue"
        
        workflow = StateGraph(ConversationState)
        workflow.add_node("propose_criteria", agent_propose_criteria)
        workflow.add_node("select_criteria", director_select_criteria)
        
        workflow.set_entry_point("propose_criteria")
        
        # propose_criteria를 반복 실행 (3명의 에이전트)
        workflow.add_conditional_edges(
            "propose_criteria",
            should_continue_proposals,
            {
                "continue": "propose_criteria",  # 다음 에이전트
                "finish": "select_criteria"      # 모두 완료 → Director 선정
            }
        )
        
        workflow.add_edge("select_criteria", END)
        
        graph = workflow.compile()
        
        # 초기 상태 생성
        initial_state = self.initialize_state(user_input)
        
        if streaming and callback:
            # 스트리밍 실행 - 상태를 누적해야 함
            accumulated_state = {**initial_state}
            for state_update in graph.stream(initial_state):
                node_name = list(state_update.keys())[0]
                node_state = state_update[node_name]
                # 상태 누적 (새로운 키-값들을 기존 상태에 추가)
                accumulated_state.update(node_state)
                
                # DEBUG: 어떤 키가 업데이트되었는지 확인
                print(f"[DEBUG workflow_engine] {node_name} 업데이트된 키: {list(node_state.keys())}")
                if 'round1_director_decision' in node_state:
                    print(f"[DEBUG workflow_engine] round1_director_decision in node_state: {bool(node_state['round1_director_decision'])}")
                
                callback(node_name, node_state)
            
            print(f"[DEBUG workflow_engine] accumulated_state 최종 키: {list(accumulated_state.keys())}")
            print(f"[DEBUG workflow_engine] 'round1_director_decision' in accumulated_state: {'round1_director_decision' in accumulated_state}")
            
            return accumulated_state
        else:
            # 일반 실행
            final_state = graph.invoke(initial_state)
            print(f"[DEBUG workflow_engine NON-STREAM] final_state 키: {list(final_state.keys())}")
            print(f"[DEBUG workflow_engine NON-STREAM] 'round1_director_decision' in final_state: {'round1_director_decision' in final_state}")
            return final_state
    
    def run_round2(
        self,
        prev_state: Dict[str, Any],
        streaming: bool = False,
        callback = None
    ) -> Dict[str, Any]:
        """
        Round 2: AHP 쌍대비교 및 가중치 계산
        
        Args:
            prev_state: Round 1 결과 상태
            streaming: 스트리밍 모드 사용 여부
            callback: 진행 상황 콜백 함수
            
        Returns:
            Round 2 완료 상태
        """
        # Round 2만을 위한 그래프 생성
        workflow = StateGraph(ConversationState)
        workflow.add_node("compare_criteria", self._compare_criteria_wrapper)
        workflow.add_node("consensus_comparison", director_consensus_comparison)
        workflow.add_node("calculate_ahp", calculate_ahp_weights)
        
        workflow.set_entry_point("compare_criteria")
        workflow.add_edge("compare_criteria", "consensus_comparison")
        workflow.add_conditional_edges(
            "consensus_comparison",
            should_continue_comparisons,
            {
                "continue": "compare_criteria",
                "finish": "calculate_ahp"
            }
        )
        workflow.add_edge("calculate_ahp", END)
        
        graph = workflow.compile()
        
        # 이전 상태 복원 + 에이전트 재생성
        state = self._restore_state_for_round2(prev_state)
        
        if streaming and callback:
            # 스트리밍 실행
            final_state = None
            for state_update in graph.stream(state):
                node_name = list(state_update.keys())[0]
                state = state_update[node_name]
                callback(node_name, state)
                final_state = state
            return final_state
        else:
            # 일반 실행
            return graph.invoke(state)
    
    def run_round3(
        self,
        prev_state: Dict[str, Any],
        streaming: bool = False,
        callback = None
    ) -> Dict[str, Any]:
        """
        Round 3: 전공별 점수 부여
        
        Args:
            prev_state: Round 2 결과 상태
            streaming: 스트리밍 모드 사용 여부
            callback: 진행 상황 콜백 함수
            
        Returns:
            Round 3 완료 상태
        """
        # Round 3만을 위한 그래프 생성
        workflow = StateGraph(ConversationState)
        workflow.add_node("score_alternative", self._score_alternative_wrapper)
        workflow.add_node("consensus_score", director_final_scoring)
        
        workflow.set_entry_point("score_alternative")
        workflow.add_edge("score_alternative", "consensus_score")
        workflow.add_edge("consensus_score", END)
        
        graph = workflow.compile()
        
        # 이전 상태 복원 + 에이전트 재생성
        state = self._restore_state_for_round3(prev_state)
        
        if streaming and callback:
            # 스트리밍 실행
            final_state = None
            for state_update in graph.stream(state):
                node_name = list(state_update.keys())[0]
                state = state_update[node_name]
                callback(node_name, state)
                final_state = state
            return final_state
        else:
            # 일반 실행
            return graph.invoke(state)
    
    def run_round4(
        self,
        prev_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Round 4: TOPSIS 최종 순위 계산 (LLM 사용 안 함)
        
        Args:
            prev_state: Round 3 결과 상태
            
        Returns:
            Round 4 완료 상태 (최종 순위 포함)
        """
        # Round 4는 LLM 사용 안 함 (계산만)
        from workflows.round4_topsis import calculate_topsis_ranking, build_decision_matrix
        
        # 이전 상태 복원
        state = self._restore_state_for_round4(prev_state)
        
        # decision_matrix가 없으면 구축
        if 'decision_matrix' not in state or not state['decision_matrix']:
            state = build_decision_matrix(state)
        
        # TOPSIS 계산
        state = calculate_topsis_ranking(state)
        
        return state
    
    # ========== 상태 복원 헬퍼 메서드 ==========
    
    def _restore_state_for_round2(self, prev_state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 2를 위한 상태 복원"""
        # Round 2에 필요한 필드 복원
        state = {
            'session_id': prev_state.get('session_id'),
            'user_input': prev_state.get('user_input'),
            'alternatives': prev_state.get('alternatives'),
            'selected_criteria': prev_state.get('selected_criteria', []),
            'agent_personas': prev_state.get('agent_personas', []),
            'round1_proposals': prev_state.get('round1_proposals', []),
            'round1_director_decision': prev_state.get('round1_director_decision', {}),
            'conversation_turns': prev_state.get('conversation_turns', 0),
            'max_criteria': self.max_criteria,
            
            # Round 2 초기화
            'round2_comparisons': {},
            'round2_director_decisions': {},
            'current_comparison_pair': None,
            
            'errors': [],
            'warnings': []
        }
        
        return state
    
    def _restore_state_for_round3(self, prev_state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 3를 위한 상태 복원"""
        # tuple 키를 가진 딕셔너리 복원
        round2_comparisons = {}
        for key, value in prev_state.get('round2_comparisons', {}).items():
            if isinstance(key, str) and '||' in key:
                parts = key.split('||')
                round2_comparisons[(parts[0], parts[1])] = value
            else:
                round2_comparisons[key] = value
        
        round2_director_decisions = {}
        for key, value in prev_state.get('round2_director_decisions', {}).items():
            if isinstance(key, str) and '||' in key:
                parts = key.split('||')
                round2_director_decisions[(parts[0], parts[1])] = value
            else:
                round2_director_decisions[key] = value
        
        # Round 3에 필요한 필드 복원
        state = {
            'session_id': prev_state.get('session_id'),
            'user_input': prev_state.get('user_input'),
            'alternatives': prev_state.get('alternatives'),
            'selected_criteria': prev_state.get('selected_criteria', []),
            'agent_personas': prev_state.get('agent_personas', []),
            'criteria_weights': prev_state.get('criteria_weights', {}),
            'consistency_ratio': prev_state.get('consistency_ratio'),
            'conversation_turns': prev_state.get('conversation_turns', 0),
            'max_criteria': self.max_criteria,
            
            # Round 1, 2 결과
            'round1_proposals': prev_state.get('round1_proposals', []),
            'round1_director_decision': prev_state.get('round1_director_decision', {}),
            'round2_comparisons': round2_comparisons,
            'round2_director_decisions': round2_director_decisions,
            
            # Round 3 초기화
            'round3_scores': {},
            'round3_director_decisions': {},
            'current_scoring_item': None,
            
            'errors': [],
            'warnings': []
        }
        
        return state
    
    def _restore_state_for_round4(self, prev_state: Dict[str, Any]) -> Dict[str, Any]:
        """Round 4를 위한 상태 복원"""
        # tuple 키를 가진 딕셔너리 복원
        round3_scores = {}
        for key, value in prev_state.get('round3_scores', {}).items():
            if isinstance(key, str) and '||' in key:
                parts = key.split('||')
                round3_scores[(parts[0], parts[1])] = value
            else:
                round3_scores[key] = value
        
        round3_director_decisions = {}
        for key, value in prev_state.get('round3_director_decisions', {}).items():
            if isinstance(key, str) and '||' in key:
                parts = key.split('||')
                round3_director_decisions[(parts[0], parts[1])] = value
            else:
                round3_director_decisions[key] = value
        
        # Round 4에 필요한 필드 복원
        state = {
            'session_id': prev_state.get('session_id'),
            'user_input': prev_state.get('user_input'),
            'alternatives': prev_state.get('alternatives'),
            'selected_criteria': prev_state.get('selected_criteria', []),
            'criteria_weights': prev_state.get('criteria_weights', {}),
            'decision_matrix': prev_state.get('decision_matrix', {}),
            'conversation_turns': prev_state.get('conversation_turns', 0),
            
            # Round 3 결과
            'round3_scores': round3_scores,
            'round3_director_decisions': round3_director_decisions,
            
            'errors': [],
            'warnings': []
        }
        
        return state
