"""Round 2 Debate System"""

import json
from pathlib import Path
from workflows.round2_ahp import run_round2_debate

USER_INPUT_PATH = 'data/user_inputs/current_user.json'

def run_round2():
    """Round 2 토론 실행"""
    
    # Round 1 결과 로드 (가장 최근 파일 - 생성 시간 기준)
    output_dir = Path("output")
    round1_files = sorted(output_dir.glob("round1_*.json"), key=lambda x: x.stat().st_mtime)
    
    if not round1_files:
        print("[ERROR] Round 1 결과 파일이 없습니다. 먼저 Round 1을 실행하세요.")
        return
    
    latest_round1 = round1_files[-1]
    print(f"[LOAD] Round 1 결과 로드: {latest_round1.name}")
    
    with open(latest_round1, 'r', encoding='utf-8') as f:
        round1_state = json.load(f)
    
    # 필요한 정보 추출 (alternatives는 user_input에서)
    state = {
        'user_input': round1_state.get('user_input', {}),
        'agent_personas': round1_state.get('agent_personas', []),
        'selected_criteria': round1_state.get('selected_criteria', [])
    }
    
    print(f"\n[Round 1] 선정된 기준: {len(state['selected_criteria'])}개")
    for i, criterion in enumerate(state['selected_criteria'], 1):
        if isinstance(criterion, dict):
            print(f"  {i}. {criterion.get('name', criterion)}")
        else:
            print(f"  {i}. {criterion}")
    
    print(f"\n[Agent Personas]")
    for persona in state['agent_personas']:
        print(f"  - {persona['name']}: {', '.join(persona['core_values'][:2])}")
    
    print(f"\n[Round 2] 토론 시작...\n")
    
    # Round 2 실행
    try:
        result_state = run_round2_debate(state)
        
        # 결과 출력
        debate_turns = result_state.get('round2_debate_turns', [])
        print(f"\n[Round 2 완료] 총 {len(debate_turns)}턴 생성")
        
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
            
            if turn_type == 'proposal' and turn.get('comparison_matrix'):
                matrix = turn['comparison_matrix']
                print(f"  Matrix: {len(matrix)}개 쌍 비교")
                # 첫 3개만 샘플 출력
                for i, (pair, value) in enumerate(list(matrix.items())[:3]):
                    print(f"    - {pair}: {value}")
                if len(matrix) > 3:
                    print(f"    ... 외 {len(matrix)-3}개")
        
        # 최종 비교 행렬
        final_matrix = result_state.get('comparison_matrix', {})
        print(f"\n[최종 비교 행렬] {len(final_matrix)}개 쌍")
        for pair, value in final_matrix.items():
            print(f"  - {pair}: {value}")
        
        # AHP 가중치는 run_round2_debate 내부에서 이미 계산됨
        print(f"\n{'='*60}")
        print("[AHP 가중치 계산은 토론 함수 내부에서 완료되었습니다]")
        print(f"{'='*60}")
        
        # 결과 저장 (alternatives 제외)
        session_id = latest_round1.stem.split('_')[-1]
        output_file = output_dir / f"round2_{session_id}.json"
        
        # alternatives 필드 제외한 상태 저장
        save_state = {k: v for k, v in result_state.items() if k != 'alternatives'}
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_state, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SAVE] 결과 저장: {output_file.name}")
        
        # AHP 가중치 출력
        criteria_weights = result_state.get('criteria_weights', {})
        cr = result_state.get('consistency_ratio', 0)
        lambda_max = result_state.get('eigenvalue_max', 0)
        
        if criteria_weights:
            print(f"\n{'='*60}")
            print("AHP 가중치 계산 결과:")
            print('='*60)
            print(f"Consistency Ratio (CR): {cr:.4f}")
            print(f"Lambda Max: {lambda_max:.4f}")
            print(f"\n기준별 가중치:")
            for criterion, weight in criteria_weights.items():
                print(f"  - {criterion}: {weight:.4f} ({weight*100:.2f}%)")
            print('='*60)
        
        # Director의 최종 결정 전문 출력
        director_decision = result_state.get('round2_director_decision', {})
        if director_decision:
            print(f"\n{'='*60}")
            print("Director 최종 결정:")
            print('='*60)
            print(director_decision.get('content', 'N/A'))
            print('='*60)
        
    except Exception as e:
        print(f"\n[ERROR] 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_round2()
