"""전공 우선순위 분석 시스템 - 라운드별 실행"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from config import Config
from core import WorkflowEngine
from models import load_user_input, format_final_output


def format_conversation_for_frontend(final_state: Dict[str, Any], round_num: int) -> Dict[str, Any]:
    """
    프론트엔드에 전달할 수 있는 대화 형식으로 변환
    
    Args:
        final_state: 라운드 실행 후 최종 상태
        round_num: 라운드 번호 (1, 2, 3, 4)
        
    Returns:
        {
            "success": True,
            "session_id": str,
            "round": int,
            "conversation": [
                {
                    "turn": int,
                    "agent": str,
                    "message": str,
                    "data": {...}  # 에이전트별 추가 데이터
                }
            ],
            "result": {...},  # 라운드별 최종 결과
            "metadata": {...}
        }
    """
    conversation = []
    result = {}
    
    if round_num == 1:
        # Round 1: 각 에이전트의 기준 제안
        for idx, proposal in enumerate(final_state.get('round1_proposals', []), 1):
            conversation.append({
                "turn": idx,
                "agent": proposal['agent_name'],
                "message": proposal['criteria'],
                "data": {
                    "proposal_type": "criteria"
                }
            })
        
        # DirectorAgent 결정
        director_decision = final_state.get('round1_director_decision', {})
        if director_decision:
            conversation.append({
                "turn": len(conversation) + 1,
                "agent": "DirectorAgent",
                "message": director_decision.get('response', ''),
                "data": {
                    "selected_criteria": director_decision.get('selected_criteria', [])
                }
            })
        
        result = {
            "selected_criteria": final_state.get('selected_criteria', []),
            "total_proposals": len(final_state.get('round1_proposals', []))
        }
    
    elif round_num == 2:
        # Round 2: AHP 가중치 대화
        for idx, comparison in enumerate(final_state.get('round2_comparisons', []), 1):
            conversation.append({
                "turn": idx,
                "agent": comparison.get('agent_name', 'Agent'),
                "message": comparison.get('rationale', ''),
                "data": {
                    "comparison_type": "pairwise",
                    "criteria_pair": comparison.get('criteria_pair', []),
                    "score": comparison.get('score', 0)
                }
            })
        
        result = {
            "criteria_weights": final_state.get('criteria_weights', {}),
            "consistency_ratio": final_state.get('consistency_ratio', 0)
        }
    
    elif round_num == 3:
        # Round 3: 대안 점수 매기기
        for idx, scoring in enumerate(final_state.get('round3_scores', []), 1):
            conversation.append({
                "turn": idx,
                "agent": scoring.get('agent_name', 'Agent'),
                "message": scoring.get('rationale', ''),
                "data": {
                    "scoring_type": "alternative",
                    "alternative": scoring.get('alternative', ''),
                    "criterion": scoring.get('criterion', ''),
                    "score": scoring.get('score', 0)
                }
            })
        
        result = {
            "score_matrix": final_state.get('score_matrix', {}),
            "alternatives": final_state.get('alternatives', {}).get('majors', [])
        }
    
    elif round_num == 4:
        # Round 4: TOPSIS 계산 (LLM 없음, 계산 결과만)
        result = {
            "final_ranking": final_state.get('final_ranking', []),
            "normalized_scores": final_state.get('normalized_scores', {}),
            "weighted_matrix": final_state.get('weighted_matrix', {})
        }
    
    return {
        "success": True,
        "session_id": final_state.get('session_id'),
        "round": round_num,
        "conversation": conversation,
        "result": result,
        "metadata": {
            "total_turns": final_state.get('conversation_turns', 0),
            "timestamp": final_state.get('timestamp', '')
        }
    }


def save_output(data: Dict[str, Any], filepath: Path):
    """JSON 결과 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"[OK] 결과가 저장되었습니다: {filepath}")


def save_summary_report(state: Dict[str, Any], filepath: Path):
    """요약 보고서 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 전공 우선순위 분석 보고서\n\n")
        f.write(f"세션 ID: {state.get('session_id')}\n\n")
        f.write(f"## 최종 순위\n\n")
        for rank_info in state.get('final_ranking', []):
            if isinstance(rank_info, tuple):
                major, score = rank_info
                f.write(f"- {major}: {score:.4f}\n")
            else:
                rank = rank_info.get('rank', '?')
                major = rank_info.get('major', '?')
                closeness = rank_info.get('closeness_coefficient', 0)
                f.write(f"{rank}위. {major} (근접도: {closeness:.4f})\n")
    print(f"[OK] 요약 보고서가 저장되었습니다: {filepath}")


def print_progress(node_name: str, state: Dict[str, Any]):
    """진행 상황 출력"""
    turns = state.get('conversation_turns', 0)
    print(f"\n{'='*60}")
    print(f"[{node_name}] (대화 턴: {turns})")
    print('='*60)
    
    # Round 1 제안 출력 (개별 에이전트, 실시간 출력)
    if node_name == 'propose_criteria':
        proposals = state.get('round1_proposals', [])
        if proposals:
            # 가장 최근 제안만 출력 (마지막 에이전트)
            latest_proposal = proposals[-1]
            print(f"\n{'─'*60}")
            print(f"[{latest_proposal['agent_name']}]")
            print('─'*60)
            print(latest_proposal['criteria'])  # 전체 출력
    
    # Round 1 선정 출력
    elif node_name == 'select_criteria':
        # DirectorAgent의 전체 응답 출력
        if 'round1_director_decision' in state and state['round1_director_decision']:
            decision = state['round1_director_decision']
            response = decision.get('response', '')
            if response:
                print(f"\n{'─'*60}")
                print(f"[DirectorAgent - 최종 선정]")
                print('─'*60)
                print(response)
        
        # 선정된 기준 요약
        if 'selected_criteria' in state:
            print(f"\n{'='*60}")
            print(f"최종 선정된 기준: {', '.join(state['selected_criteria'])}")
            print('='*60)
    
    # Round 2 비교 출력 (전체 내용 표시)
    elif node_name == 'compare_criteria':
        if 'current_comparison_pair' in state and state['current_comparison_pair']:
            pair = state['current_comparison_pair']
            print(f"\n비교 쌍: {pair[0]} vs {pair[1]}")
            if 'round2_comparisons' in state and pair in state['round2_comparisons']:
                for resp in state['round2_comparisons'][pair]:
                    response = resp.get('response', '')
                    print(f"\n{'─'*60}")
                    print(f"[{resp['agent_name']}]")
                    print('─'*60)
                    print(response)  # 전체 출력
    
    # Round 3 점수 출력
    elif node_name == 'score_alternative':
        if 'current_scoring_item' in state and state['current_scoring_item']:
            major, criterion = state['current_scoring_item']
            print(f"\n점수 항목: {major} - {criterion}")
            if 'round3_scores' in state and (major, criterion) in state['round3_scores']:
                for resp in state['round3_scores'][(major, criterion)]:
                    print(f"\n[{resp['agent_name']}] {resp.get('score', 'N/A')}점")


def load_state(session_id: str, round_num: int) -> Dict[str, Any]:
    """이전 라운드 결과 로드"""
    state_path = Config.OUTPUT_DIR / f"state_{session_id}_round{round_num}.json"
    
    if not state_path.exists():
        raise FileNotFoundError(f"상태 파일을 찾을 수 없습니다: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state: Dict[str, Any], session_id: str, round_num: int):
    """현재 라운드 결과 저장"""
    state_path = Config.OUTPUT_DIR / f"state_{session_id}_round{round_num}.json"
    
    # 간소화된 상태 저장 (에이전트 인스턴스 제외)
    save_data = {
        'session_id': session_id,
        'round': round_num,
        'timestamp': datetime.now().isoformat(),
        'user_input': state.get('user_input'),
        'alternatives': state.get('alternatives'),
        'conversation_turns': state.get('conversation_turns', 0)
    }
    
    # Round별 데이터 추가
    if round_num >= 1:
        save_data['round1_proposals'] = state.get('round1_proposals', [])
        save_data['selected_criteria'] = state.get('selected_criteria', [])
        save_data['round1_director_decision'] = state.get('round1_director_decision', {})
    
    if round_num >= 2:
        # dict를 JSON serializable하게 변환 (tuple 키 처리)
        comparisons = state.get('round2_comparisons', {})
        save_data['round2_comparisons'] = {f"{k[0]}||{k[1]}": v for k, v in comparisons.items() if isinstance(k, tuple)}
        
        decisions = state.get('round2_director_decisions', {})
        save_data['round2_director_decisions'] = {f"{k[0]}||{k[1]}": v for k, v in decisions.items() if isinstance(k, tuple)}
        
        save_data['criteria_weights'] = state.get('criteria_weights', {})
        save_data['consistency_ratio'] = state.get('consistency_ratio')
    
    if round_num >= 3:
        scores = state.get('round3_scores', {})
        save_data['round3_scores'] = {f"{k[0]}||{k[1]}": v for k, v in scores.items() if isinstance(k, tuple)}
        
        decisions = state.get('round3_director_decisions', {})
        save_data['round3_director_decisions'] = {f"{k[0]}||{k[1]}": v for k, v in decisions.items() if isinstance(k, tuple)}
        
        save_data['decision_matrix'] = state.get('decision_matrix', {})
    
    if round_num >= 4:
        save_data['topsis_results'] = state.get('topsis_results', [])
        save_data['final_ranking'] = state.get('final_ranking', [])
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n[OK] 상태 저장 완료: {state_path}")
    
    # 프론트엔드용 대화 형식도 저장
    frontend_data = format_conversation_for_frontend(state, round_num)
    frontend_path = Config.OUTPUT_DIR / f"conversation_{session_id}_round{round_num}.json"
    with open(frontend_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"[OK] 대화 데이터 저장 완료: {frontend_path}")



def run_round1(input_path: str, streaming: bool):
    """Round 1: 평가 기준 제안 및 선정"""
    print("\n[INFO] Round 1: 평가 기준 제안 및 선정")
    
    # 사용자 입력 로드
    if input_path is None:
        input_path = Config.INPUT_DIR / "sample_template.json"
    else:
        input_path = Path(input_path)
    
    print(f"\n[INFO] 입력 파일: {input_path}")
    
    try:
        user_input = load_user_input(str(input_path))
        print("[OK] 사용자 입력 검증 완료")
        alternatives = user_input.get('alternatives', {})
        if 'majors' in alternatives:
            print(f"   - 평가 대상: majors")
        agent_config = user_input.get('agent_config', {})
        print(f"   - 가중치: Value {agent_config.get('value_weight', 0)}, Fit {agent_config.get('fit_weight', 0)}, Market {agent_config.get('market_weight', 0)}")
    except Exception as e:
        print(f"\n[ERROR] 입력 파일 로드 실패: {e}")
        sys.exit(1)
    
    # 워크플로우 엔진 초기화
    print(f"\n[INFO] 워크플로우 엔진 초기화 중...")
    engine = WorkflowEngine(
        model_name=Config.OPENAI_MODEL,
        agent_temperature=Config.AGENT_TEMPERATURE,
        director_temperature=Config.DIRECTOR_TEMPERATURE,
        max_criteria=Config.MAX_CRITERIA
    )
    print("[OK] 엔진 초기화 완료")
    
    # Round 1 실행
    print(f"\n[INFO] Round 1 실행 시작...")
    print("=" * 60)
    
    try:
        final_state = engine.run_round1(user_input, streaming, print_progress if streaming else None)
        
        # 스트리밍 모드 후 DirectorAgent 최종 응답 출력
        print(f"[DEBUG] streaming={streaming}")
        print(f"[DEBUG] 'round1_director_decision' in final_state: {'round1_director_decision' in final_state}")
        if 'round1_director_decision' in final_state:
            print(f"[DEBUG] final_state['round1_director_decision']: {final_state['round1_director_decision']}")
        
        if streaming and 'round1_director_decision' in final_state and final_state['round1_director_decision']:
            decision = final_state['round1_director_decision']
            response = decision.get('response', '')
            print(f"[DEBUG] response 길이: {len(response)}")
            if response:
                print(f"\n{'='*60}")
                print(f"[DirectorAgent - 최종 결정]")
                print('='*60)
                print(response)
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("Round 1 완료")
        print("=" * 60)
        print(f"\n선정된 기준: {', '.join(final_state.get('selected_criteria', []))}")
        print(f"총 대화 턴: {final_state.get('conversation_turns', 0)}")
        
        # 상태 저장
        session_id = final_state.get('session_id')
        save_state(final_state, session_id, 1)
        
        print(f"\n다음 단계: python main.py --round 2 --session {session_id}")
        
    except Exception as e:
        print(f"\n[ERROR] Round 1 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_round2(session_id: str, streaming: bool):
    """Round 2: AHP 쌍대비교 및 가중치 계산"""
    print("\n[INFO] Round 2: AHP 쌍대비교")
    
    if not session_id:
        print("\n[ERROR] 세션 ID가 필요합니다. --session 옵션을 사용하세요.")
        sys.exit(1)
    
    # Round 1 결과 로드
    try:
        print(f"\n[INFO] Round 1 결과 로드 중... (세션: {session_id})")
        prev_state = load_state(session_id, 1)
        print("[OK] Round 1 결과 로드 완료")
        print(f"   - 선정된 기준: {', '.join(prev_state.get('selected_criteria', []))}")
    except Exception as e:
        print(f"\n[ERROR] Round 1 결과 로드 실패: {e}")
        sys.exit(1)
    
    # 워크플로우 엔진 초기화
    engine = WorkflowEngine(
        model_name=Config.OPENAI_MODEL,
        agent_temperature=Config.AGENT_TEMPERATURE,
        director_temperature=Config.DIRECTOR_TEMPERATURE,
        max_criteria=Config.MAX_CRITERIA
    )
    
    # Round 2 실행
    print(f"\n[INFO] Round 2 실행 시작...")
    print("=" * 60)
    
    try:
        final_state = engine.run_round2(prev_state, streaming, print_progress if streaming else None)
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("Round 2 완료")
        print("=" * 60)
        print(f"\n기준 가중치:")
        for criterion, weight in final_state.get('criteria_weights', {}).items():
            print(f"  - {criterion}: {weight:.4f}")
        print(f"\nConsistency Ratio: {final_state.get('consistency_ratio', 0):.4f}")
        print(f"총 대화 턴: {final_state.get('conversation_turns', 0)}")
        
        # 상태 저장
        save_state(final_state, session_id, 2)
        
        print(f"\n다음 단계: python main.py --round 3 --session {session_id}")
        
    except Exception as e:
        print(f"\n[ERROR] Round 2 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_round3(session_id: str, streaming: bool):
    """Round 3: 전공별 점수 부여"""
    print("\n[INFO] Round 3: 전공별 점수 부여")
    
    if not session_id:
        print("\n[ERROR] 세션 ID가 필요합니다. --session 옵션을 사용하세요.")
        sys.exit(1)
    
    # Round 2 결과 로드
    try:
        print(f"\n[INFO] Round 2 결과 로드 중... (세션: {session_id})")
        prev_state = load_state(session_id, 2)
        print("[OK] Round 2 결과 로드 완료")
    except Exception as e:
        print(f"\n[ERROR] Round 2 결과 로드 실패: {e}")
        sys.exit(1)
    
    # 워크플로우 엔진 초기화
    engine = WorkflowEngine(
        model_name=Config.OPENAI_MODEL,
        agent_temperature=Config.AGENT_TEMPERATURE,
        director_temperature=Config.DIRECTOR_TEMPERATURE,
        max_criteria=Config.MAX_CRITERIA
    )
    
    # Round 3 실행
    print(f"\n[INFO] Round 3 실행 시작...")
    print("=" * 60)
    
    try:
        final_state = engine.run_round3(prev_state, streaming, print_progress if streaming else None)
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("Round 3 완료")
        print("=" * 60)
        print(f"\n의사결정 매트릭스 구축 완료")
        print(f"총 대화 턴: {final_state.get('conversation_turns', 0)}")
        
        # 상태 저장
        save_state(final_state, session_id, 3)
        
        print(f"\n다음 단계: python main.py --round 4 --session {session_id}")
        
    except Exception as e:
        print(f"\n[ERROR] Round 3 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_round4(session_id: str):
    """Round 4: TOPSIS 최종 순위 계산"""
    print("\n[INFO] Round 4: TOPSIS 최종 순위 계산")
    
    if not session_id:
        print("\n[ERROR] 세션 ID가 필요합니다. --session 옵션을 사용하세요.")
        sys.exit(1)
    
    # Round 3 결과 로드
    try:
        print(f"\n[INFO] Round 3 결과 로드 중... (세션: {session_id})")
        prev_state = load_state(session_id, 3)
        print("[OK] Round 3 결과 로드 완료")
    except Exception as e:
        print(f"\n[ERROR] Round 3 결과 로드 실패: {e}")
        sys.exit(1)
    
    # 워크플로우 엔진 초기화
    engine = WorkflowEngine(
        model_name=Config.OPENAI_MODEL,
        agent_temperature=Config.AGENT_TEMPERATURE,
        director_temperature=Config.DIRECTOR_TEMPERATURE,
        max_criteria=Config.MAX_CRITERIA
    )
    
    # Round 4 실행
    print(f"\n[INFO] Round 4 실행 시작...")
    print("=" * 60)
    
    try:
        final_state = engine.run_round4(prev_state)
        
        # 최종 순위 출력
        print("\n" + "=" * 60)
        print("최종 순위")
        print("=" * 60)
        
        for rank_info in final_state.get('final_ranking', []):
            if isinstance(rank_info, tuple):
                major, score = rank_info
                print(f"{major}: {score:.4f}")
            else:
                rank = rank_info.get('rank', '?')
                major = rank_info.get('major', '?')
                closeness = rank_info.get('closeness_coefficient', 0)
                print(f"{rank}위. {major} (근접도: {closeness:.4f})")
        
        # 상태 저장
        save_state(final_state, session_id, 4)
        
        # 최종 결과 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = format_final_output(final_state)
        output_path = Config.OUTPUT_DIR / f"result_{session_id}_{timestamp}.json"
        save_output(output, output_path)
        
        report_path = Config.OUTPUT_DIR / f"report_{session_id}_{timestamp}.md"
        save_summary_report(final_state, report_path)
        
        print("\n" + "=" * 60)
        print("분석 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Round 4 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main(input_path: str = None, round_num: int = 1, session_id: str = None, streaming: bool = False):
    """
    메인 실행 함수 - 라운드별 실행
    
    Args:
        input_path: 입력 JSON 파일 경로 (Round 1에만 필요)
        round_num: 실행할 라운드 번호 (1~4)
        session_id: 세션 ID (Round 2~4에서 이전 결과 로드)
        streaming: 스트리밍 모드 사용 여부
    """
    print("=" * 60)
    print(f"전공 우선순위 분석 시스템 - Round {round_num}")
    print("=" * 60)
    
    # 1. 환경 설정 확인
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n[ERROR] 설정 오류: {e}")
        print(".env 파일을 확인하거나 환경 변수를 설정하세요.")
        sys.exit(1)
    
    # 2. Round별 실행
    if round_num == 1:
        run_round1(input_path, streaming)
    elif round_num == 2:
        run_round2(session_id, streaming)
    elif round_num == 3:
        run_round3(session_id, streaming)
    elif round_num == 4:
        run_round4(session_id)
    else:
        print(f"\n[ERROR] 잘못된 라운드 번호: {round_num}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="전공 우선순위 분석 시스템")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="사용자 입력 JSON 파일 경로 (Round 1에만 필요)"
    )
    parser.add_argument(
        "--round",
        "-r",
        type=int,
        choices=[1, 2, 3, 4],
        required=True,
        help="실행할 라운드 (1: 기준 선정, 2: AHP, 3: 점수 부여, 4: TOPSIS)"
    )
    parser.add_argument(
        "--session",
        "-sid",
        type=str,
        help="세션 ID (Round 2~4에서 이전 결과 로드용)"
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="스트리밍 모드 사용"
    )
    
    args = parser.parse_args()
    
    main(
        input_path=args.input,
        round_num=args.round,
        session_id=args.session,
        streaming=args.stream
    )
