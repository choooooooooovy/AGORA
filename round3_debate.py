"""Round 3 Debate System"""

import json
from pathlib import Path
from workflows.round3_scoring import run_round3_debate

USER_INPUT_PATH = 'data/user_inputs/current_user.json'

def run_round3():
    """Round 3 토론 실행"""
    
    # Round 2 결과 로드 (가장 최근 파일 - 생성 시간 기준)
    output_dir = Path("output")
    round2_files = sorted(output_dir.glob("round2_*.json"), key=lambda x: x.stat().st_mtime)
    
    if not round2_files:
        print("[ERROR] Round 2 결과 파일이 없습니다. 먼저 Round 2를 실행하세요.")
        return
    
    latest_round2 = round2_files[-1]
    print(f"[LOAD] Round 2 결과 로드: {latest_round2.name}")
    
    with open(latest_round2, 'r', encoding='utf-8') as f:
        round2_state = json.load(f)
    
    # 필요한 정보 추출
    state = {
        'user_input': round2_state.get('user_input', {}),
        'alternatives': round2_state.get('alternatives', []),  # Round 2에서 전달된 alternatives 사용
        'agent_personas': round2_state.get('agent_personas', []),
        'selected_criteria': round2_state.get('selected_criteria', []),
        'criteria_weights': round2_state.get('criteria_weights', {})
    }
    
    print(f"\n[Round 2] 기준 가중치:")
    for criterion, weight in state['criteria_weights'].items():
        print(f"  - {criterion}: {weight:.4f}")
    
    print(f"\n[평가 대상] {len(state['alternatives'])}개 전공")
    for i, alt in enumerate(state['alternatives'], 1):
        print(f"  {i}. {alt}")
    
    print(f"\n[Agent Personas]")
    for persona in state['agent_personas']:
        print(f"  - {persona['name']}: {', '.join(persona['core_values'][:2])}")
    
    print(f"\n[Round 3] 토론 시작...\n")
    
    # Round 3 실행
    try:
        result_state = run_round3_debate(state)
        
        # 결과 출력
        debate_turns = result_state.get('round3_debate_turns', [])
        print(f"\n[Round 3 완료] 총 {len(debate_turns)}턴 생성")
        
        # 각 턴 요약
        for turn in debate_turns:
            turn_num = turn.get('turn', '?')
            phase = turn.get('phase', '?')
            speaker = turn.get('speaker', '?')
            turn_type = turn.get('type', '?')
            content_preview = turn.get('content', '')[:100].replace('\n', ' ')
            
            print(f"\n[Turn {turn_num}] {phase}")
            print(f"  Speaker: {speaker} ({turn_type})")
            print(f"  Content: {content_preview}...")
            
            if turn_type == 'proposal' and turn.get('decision_matrix'):
                matrix = turn['decision_matrix']
                print(f"  Matrix: {len(matrix)}개 전공")
                # 첫 2개 전공만 샘플 출력
                for i, (major, scores) in enumerate(list(matrix.items())[:2]):
                    print(f"    [{major}]")
                    for j, (criterion, score) in enumerate(list(scores.items())[:3]):
                        print(f"      - {criterion}: {score}")
                    if len(scores) > 3:
                        print(f"      ... 외 {len(scores)-3}개")
        
        # 최종 Decision Matrix
        final_matrix = result_state.get('decision_matrix', {})
        print(f"\n{'='*80}")
        print("최종 Decision Matrix")
        print('='*80)
        
        # 기준 이름 추출
        criteria_names = list(state['criteria_weights'].keys())
        
        # 헤더 출력
        print(f"\n{'전공':<20}", end='')
        for criterion in criteria_names:
            print(f"{criterion[:15]:<17}", end='')
        print()
        print('-' * 80)
        
        # 각 전공별 점수 출력
        for major in state['alternatives']:
            print(f"{major:<20}", end='')
            if major in final_matrix:
                for criterion in criteria_names:
                    score = final_matrix[major].get(criterion, 'N/A')
                    print(f"{score:<17}", end='')
            print()
        
        print('='*80)
        
        # 점수 통계
        all_scores = []
        for major_scores in final_matrix.values():
            all_scores.extend(major_scores.values())
        
        if all_scores:
            print(f"\n[점수 통계]")
            print(f"  총 평가 개수: {len(all_scores)}개")
            print(f"  평균: {sum(all_scores)/len(all_scores):.2f}")
            print(f"  최소: {min(all_scores):.1f}")
            print(f"  최대: {max(all_scores):.1f}")
            
            # 점수 분포
            from collections import Counter
            score_dist = Counter(all_scores)
            print(f"\n[점수 분포]")
            for score in sorted(score_dist.keys()):
                count = score_dist[score]
                bar = '█' * count
                print(f"  {score:.1f}: {bar} ({count}개)")
        
        # 결과 저장
        session_id = latest_round2.stem.split('_')[-1]
        output_file = output_dir / f"round3_{session_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_state, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SAVE] 결과 저장: {output_file.name}")
        
        # Director의 최종 결정 이유 출력
        director_decision = result_state.get('round3_director_decision', {})
        if director_decision and director_decision.get('reasoning'):
            print(f"\n{'='*80}")
            print("Director 최종 결정 이유:")
            print('='*80)
            print(director_decision.get('reasoning', 'N/A'))
            print('='*80)
        
    except Exception as e:
        print(f"\n[ERROR] Round 3 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_round3()
