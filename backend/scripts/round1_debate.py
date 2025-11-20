"""Round 1 Debate System"""

import json
import os
import sys
from dotenv import load_dotenv
from core.workflow_engine import WorkflowEngine
from models.user_input_schema import UserInput

# API 키 로드
load_dotenv()

# Command line argument로 session_id 받기
if len(sys.argv) < 2:
    print("Usage: python round1_debate.py <session_id>")
    sys.exit(1)

session_id = sys.argv[1]

# 사용자 데이터 로드 (session_id 기반)
USER_INPUT_PATH = f'data/user_inputs/{session_id}.json'
PERSONAS_PATH = f'output/personas_{session_id}.json'

if not os.path.exists(USER_INPUT_PATH):
    print(f"Error: User input file not found: {USER_INPUT_PATH}")
    sys.exit(1)

if not os.path.exists(PERSONAS_PATH):
    print(f"Error: Personas file not found: {PERSONAS_PATH}")
    print(f"Hint: Run generate_personas.py first")
    sys.exit(1)

with open(USER_INPUT_PATH, 'r', encoding='utf-8') as f:
    test_data = json.load(f)

with open(PERSONAS_PATH, 'r', encoding='utf-8') as f:
    personas_data = json.load(f)

# UserInput 검증
user_input = UserInput(**test_data)

print("=" * 80)
print("[Round 1] 토론 시스템 시작")
print("=" * 80)
print(f"[Session ID] {session_id}")
print(f"[Loaded Personas] {len(personas_data['agent_personas'])}명")
for persona in personas_data['agent_personas']:
    print(f"  - {persona['name']}: {persona['perspective']}")

# WorkflowEngine 초기화
engine = WorkflowEngine(
    model_name="gpt-4o",
    agent_temperature=0.7,
    director_temperature=0.0,
    max_criteria=5
)

# Round 1만 실행 (기존 페르소나 사용)
print("\n[1단계] 기존 페르소나 로드...")
initial_state = {
    'user_input': personas_data['user_input'],
    'agent_personas': personas_data['agent_personas'],
    'alternatives': user_input.candidate_majors,
    'agent_weights': [1.0, 1.0, 1.0],  # 균등 가중치
    'max_criteria': 5
}

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
    
    output_file = f"{output_dir}/round1_{session_id}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'session_id': session_id,
            'user_input': test_data,  # 원본 user_input 저장 (candidate_majors 포함)
            # 'alternatives' 제외: user_input.candidate_majors와 중복
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
