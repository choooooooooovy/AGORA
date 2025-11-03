"""Round 1 Debate System"""

import json
import os
from dotenv import load_dotenv
from core.workflow_engine import WorkflowEngine
from models.user_input_schema import UserInput

# API 키 로드
load_dotenv()

# 사용자 데이터 로드 (고정 경로)
USER_INPUT_PATH = 'data/user_inputs/current_user.json'
with open(USER_INPUT_PATH, 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# UserInput 검증
user_input = UserInput(**test_data)

print("=" * 80)
print("[Round 1] 토론 시스템 시작")
print("=" * 80)

# WorkflowEngine 초기화
engine = WorkflowEngine(
    model_name="gpt-4o",
    agent_temperature=0.7,
    director_temperature=0.0,
    max_criteria=5
)

# Round 1만 실행
print("\n[1단계] 초기 상태 생성 및 페르소나 생성...")
initial_state = engine.initialize_state(user_input.model_dump())

print("\n[2단계] Round 1 토론 시작...")
from workflows.round1_criteria import run_round1_debate

try:
    final_state = run_round1_debate(initial_state)
    
    print("\n" + "=" * 80)
    print("[Round 1 완료]")
    
    # 디버그: 전체 state 키 출력
    print("\n[State Keys]", list(final_state.keys()))
    
    # 디버그: debate_turns 구조 확인
    if 'round1_debate_turns' in final_state:
        print(f"[Debate Turns] {len(final_state['round1_debate_turns'])}개 턴")
        for i, turn in enumerate(final_state['round1_debate_turns'][:3], 1):
            print(f"  Turn {i}: {turn.get('speaker', 'Unknown')} - {turn.get('type', 'Unknown')}")
    
    # 선정된 기준 확인
    if 'selected_criteria' in final_state:
        print(f"\n[Selected Criteria] {len(final_state['selected_criteria'])}개")
    else:
        print("\n[WARNING] selected_criteria가 state에 없습니다!")
    
    print("\n[최종 선정된 평가 기준]")
    
    selected_criteria = final_state.get('selected_criteria', [])
    for idx, criterion in enumerate(selected_criteria, 1):
        print(f"\n{idx}. {criterion.get('name', 'N/A')}")
        print(f"   설명: {criterion.get('description', 'N/A')[:100]}...")
        print(f"   출처: {criterion.get('source_agent', 'N/A')}")
    
    # 결과 저장
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    session_id = final_state['session_id']
    output_file = f"{output_dir}/round1_{session_id}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'session_id': session_id,
            'user_input': test_data,  # 원본 user_input 저장
            'alternatives': final_state.get('alternatives', []),
            'agent_personas': final_state['agent_personas'],
            'round1_debate_turns': final_state.get('round1_debate_turns', []),
            'selected_criteria': selected_criteria,
            'round1_director_decision': final_state.get('round1_director_decision', {})
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVE] 결과 저장: {output_file}")
    
except Exception as e:
    print(f"\n[ERROR] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
