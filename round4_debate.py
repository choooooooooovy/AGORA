"""Round 4 TOPSIS 최종 순위 계산 테스트"""

import json
from pathlib import Path
from workflows.round4_topsis import calculate_topsis_ranking


USER_INPUT_PATH = 'data/user_inputs/current_user.json'

def run_round4():
    """Round 4 TOPSIS 실행"""
    
    output_dir = Path("output")
    
    # Round 3 결과 파일 찾기 (가장 최근 파일)
    round3_files = sorted(
        output_dir.glob("round3_*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not round3_files:
        print("Round 3 결과 파일을 찾을 수 없습니다.")
        return
    
    round3_file = round3_files[0]
    session_id = round3_file.stem.replace("round3_", "")
    
    print(f"\n{'='*80}")
    print("Round 4: TOPSIS 최종 순위 계산")
    print(f"{'='*80}")
    print(f"Session ID: {session_id}")
    print(f"Round 3 결과: {round3_file.name}\n")
    
    # Round 3 state 로드
    with open(round3_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    # 데이터 확인 (alternatives는 user_input에서 추출)
    alternatives = state.get('user_input', {}).get('candidate_majors', [])
    selected_criteria = state.get('selected_criteria', [])
    decision_matrix = state.get('decision_matrix', {})
    criteria_weights = state.get('criteria_weights', {})
    
    print(f"대안: {len(alternatives)}개 - {alternatives}")
    print(f"기준: {len(selected_criteria)}개")
    for criterion in selected_criteria:
        weight = criteria_weights.get(criterion['name'], 0)
        print(f"  - {criterion['name']}: {weight*100:.1f}%")
    
    print(f"\nDecision Matrix: {len(decision_matrix)} x {len(selected_criteria)}")
    
    # TOPSIS 계산
    print("\nTOPSIS 계산 중...")
    state = calculate_topsis_ranking(state)
    
    if state.get('status') == 'failed':
        print(f"\n오류 발생: {state.get('errors', [])}")
        return
    
    # 결과 출력
    topsis_result = state.get('topsis_result', {})
    ranking = topsis_result.get('ranking', [])
    
    print(f"\n{'='*80}")
    print("최종 순위")
    print(f"{'='*80}\n")
    
    for item in ranking:
        rank = item['rank']
        major = item['major']
        closeness = item['closeness_coefficient']
        
        print(f"🏆 {rank}위: {major}")
        print(f"   근접도 계수: {closeness:.4f}")
        print(f"   이상해까지 거리: {item['distance_to_ideal']:.4f}")
        print(f"   반이상해까지 거리: {item['distance_to_anti_ideal']:.4f}")
        
        # 가중 점수 출력
        print(f"   가중 점수:")
        for crit_name, weighted_score in item['weighted_scores'].items():
            original_score = item['criterion_scores'].get(crit_name, 0)
            weight = criteria_weights.get(crit_name, 0)
            print(f"     • {crit_name}: {original_score:.1f} × {weight:.3f} = {weighted_score:.4f}")
        print()
    
    # 결과 저장
    output_file = output_dir / f"round4_{session_id}.json"
    
    # 저장할 데이터 준비 (alternatives 제외)
    output_data = {
        'session_id': session_id,
        'user_input': state.get('user_input', {}),  # candidate_majors 포함
        # 'alternatives' 제외: user_input.candidate_majors와 중복
        'selected_criteria': selected_criteria,
        'criteria_weights': criteria_weights,
        'decision_matrix': decision_matrix,
        'topsis_result': topsis_result,
        'final_ranking': ranking,
        'status': state.get('status', 'success')
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*80}")
    print(f"결과 저장: {output_file.name}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_round4()
