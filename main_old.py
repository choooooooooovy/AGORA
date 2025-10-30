"""메인 실행 파일"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from config import Config
from core import WorkflowEngine
from models.user_input_schema import UserInput
from workflows.round4_topsis import format_final_output


def load_user_input(input_path: str) -> Dict[str, Any]:
    """
    사용자 입력 JSON 파일 로드 및 검증
    
    Args:
        input_path: 입력 JSON 파일 경로
        
    Returns:
        검증된 사용자 입력 딕셔너리
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Pydantic 검증
    user_input = UserInput(**data)
    
    # 딕셔너리로 변환
    return user_input.model_dump()


def save_output(output: Dict[str, Any], output_path: str):
    """
    결과를 JSON 파일로 저장
    
    Args:
        output: 출력 데이터
        output_path: 저장 경로
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 결과가 저장되었습니다: {output_path}")


def save_summary_report(state: Dict[str, Any], report_path: str):
    """
    요약 보고서를 마크다운 파일로 저장
    
    Args:
        state: 최종 상태
        report_path: 저장 경로
    """
    from workflows.round4_topsis import generate_summary_report
    
    report = generate_summary_report(state)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[OK] 요약 보고서가 저장되었습니다: {report_path}")


def print_progress(node_name: str, state: Dict[str, Any]):
    """
    진행 상황 출력
    
    Args:
        node_name: 현재 노드 이름
        state: 현재 상태
    """
    turns = state.get('conversation_turns', 0)
    print(f"\n{'='*60}")
    print(f"[{node_name}] (대화 턴: {turns})")
    print('='*60)
    
    # Round 1 제안 출력
    if node_name == 'propose_criteria' and 'round1_proposals' in state:
        for proposal in state['round1_proposals']:
            print(f"\n[{proposal['agent_name']}]")
            print(proposal['criteria'][:300] + "..." if len(proposal['criteria']) > 300 else proposal['criteria'])
    
    # Round 1 선정 출력
    elif node_name == 'select_criteria':
        if 'round1_director_decision' in state:
            decision = state['round1_director_decision']
            print(f"\n[DirectorAgent - 기준 선정]")
            print(decision['response'][:500] + "..." if len(decision['response']) > 500 else decision['response'])
            if 'selected_criteria' in state:
                print(f"\n선정된 기준: {', '.join(state['selected_criteria'])}")
    
    # Round 2 비교 출력
    elif node_name == 'compare_criteria':
        if 'current_comparison_pair' in state and state['current_comparison_pair']:
            pair = state['current_comparison_pair']
            print(f"\n비교 쌍: {pair[0]} vs {pair[1]}")
            if 'round2_comparisons' in state and pair in state['round2_comparisons']:
                for resp in state['round2_comparisons'][pair]:
                    print(f"\n[{resp['agent_name']}]")
                    print(resp['response'][:200] + "..." if len(resp['response']) > 200 else resp['response'])
    
    # Round 3 점수 출력
    elif node_name == 'score_alternative':
        if 'current_scoring_item' in state and state['current_scoring_item']:
            major, criterion = state['current_scoring_item']
            print(f"\n점수 항목: {major} - {criterion}")
            if 'round3_scores' in state and (major, criterion) in state['round3_scores']:
                for resp in state['round3_scores'][(major, criterion)]:
                    print(f"\n[{resp['agent_name']}] {resp.get('score', 'N/A')}점")


def load_state(session_id: str, round_num: int) -> Dict[str, Any]:
    """
    이전 라운드 결과 로드
    
    Args:
        session_id: 세션 ID
        round_num: 로드할 라운드 번호
        
    Returns:
        저장된 상태 딕셔너리
    """
    state_path = Config.OUTPUT_DIR / f"state_{session_id}_round{round_num}.json"
    
    if not state_path.exists():
        raise FileNotFoundError(f"상태 파일을 찾을 수 없습니다: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state: Dict[str, Any], session_id: str, round_num: int):
    """
    현재 라운드 결과 저장
    
    Args:
        state: 저장할 상태
        session_id: 세션 ID
        round_num: 라운드 번호
    """
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
        save_data['round2_comparisons'] = state.get('round2_comparisons', {})
        save_data['round2_director_decisions'] = state.get('round2_director_decisions', {})
        save_data['criteria_weights'] = state.get('criteria_weights', {})
        save_data['consistency_ratio'] = state.get('consistency_ratio')
    
    if round_num >= 3:
        save_data['round3_scores'] = state.get('round3_scores', {})
        save_data['round3_director_decisions'] = state.get('round3_director_decisions', {})
        save_data['decision_matrix'] = state.get('decision_matrix', {})
    
    if round_num >= 4:
        save_data['topsis_results'] = state.get('topsis_results', [])
        save_data['final_ranking'] = state.get('final_ranking', [])
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n[OK] 상태 저장 완료: {state_path}")


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
        print(f"   - 평가 대상: {user_input['alternatives']['majors'][0] if user_input.get('alternatives') else 'N/A'}")
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
        final_state = engine.run_round1(user_input, streaming)
        
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
        final_state = engine.run_round2(prev_state, streaming)
        
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
        final_state = engine.run_round3(prev_state, streaming)
        
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
    if not Config.validate():
        print("\n[ERROR] 설정 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
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
    
    # 1. 설정 검증
    try:
        Config.validate()
        if Config.DEBUG:
            print(Config.get_summary())
    except ValueError as e:
        print(f"[ERROR] 설정 오류: {e}")
        sys.exit(1)
    
    # 2. 입력 파일 로드
    if input_path is None:
        input_path = Config.DATA_DIR / "user_inputs" / "sample_template.json"
    
    print(f"\n[INFO] 입력 파일: {input_path}")
    
    try:
        user_input = load_user_input(input_path)
        print(f"[OK] 사용자 입력 검증 완료")
        print(f"   - 평가 대상: {', '.join(user_input['alternatives'])}")
        print(f"   - 가중치: Value {user_input['agent_config']['value_weight']}, "
              f"Fit {user_input['agent_config']['fit_weight']}, "
              f"Market {user_input['agent_config']['market_weight']}")
    except Exception as e:
        print(f"[ERROR] 입력 파일 로드 실패: {e}")
        sys.exit(1)
    
    # 3. 워크플로우 엔진 초기화
    print(f"\n[INFO] 워크플로우 엔진 초기화 중...")
    engine = WorkflowEngine(
        model_name=Config.OPENAI_MODEL,
        agent_temperature=Config.AGENT_TEMPERATURE,
        director_temperature=Config.DIRECTOR_TEMPERATURE,
        max_criteria=Config.MAX_CRITERIA
    )
    print("[OK] 엔진 초기화 완료")
    
    # 4. 워크플로우 실행
    print(f"\n[INFO] 워크플로우 실행 시작...")
    print("=" * 60)
    
    try:
        if streaming:
            # 스트리밍 모드
            final_state = None
            for node_output in engine.run_stream(user_input):
                for node_name, state in node_output.items():
                    print_progress(node_name, state)
                    final_state = state
        else:
            # 일반 모드
            final_state = engine.run(user_input)
            print(f"\n[OK] 워크플로우 실행 완료")
            print(f"   - 총 대화 턴: {final_state.get('conversation_turns', 0)}")
            print(f"   - 실행 시간: {final_state.get('execution_time', 0):.2f}초")
    
    except Exception as e:
        print(f"\n[ERROR] 워크플로우 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 5. 결과 출력
    print("\n" + "=" * 60)
    print("최종 순위")
    print("=" * 60)
    
    for rank_info in final_state.get('final_ranking', []):
        rank = rank_info['rank']
        major = rank_info['major']
        closeness = rank_info['closeness_coefficient']
        print(f"{rank}위. {major} (근접도: {closeness:.4f})")
    
    # 6. 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = final_state.get('session_id', 'unknown')
    
    # JSON 출력
    output = format_final_output(final_state)
    output_path = Config.OUTPUT_DIR / f"result_{session_id}_{timestamp}.json"
    save_output(output, output_path)
    
    # 마크다운 보고서
    report_path = Config.OUTPUT_DIR / f"report_{session_id}_{timestamp}.md"
    save_summary_report(final_state, report_path)
    
    print("\n" + "=" * 60)
    print("분석 완료!")
    print("=" * 60)


if __name__ == "__main__":
    # 커맨드라인 인자 처리
    import argparse
    
    parser = argparse.ArgumentParser(description="전공 우선순위 분석 시스템")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="사용자 입력 JSON 파일 경로"
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
