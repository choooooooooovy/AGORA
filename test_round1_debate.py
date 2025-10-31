"""Round 1 Debate System 테스트"""

import json
import os
from dotenv import load_dotenv
from core.workflow_engine import WorkflowEngine
from models.user_input_schema import UserInput

# API 키 로드
load_dotenv()

# 테스트 데이터 로드
with open('data/user_inputs/sample_template_new.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# UserInput 검증
user_input = UserInput(**test_data)

print("=" * 80)
print("🎯 Round 1 토론 시스템 테스트 시작")
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
    print("✅ Round 1 완료!")
    print("=" * 80)
    
    # 결과 출력
    debate_turns = final_state.get('round1_debate_turns', [])
    print(f"\n총 {len(debate_turns)}개 턴 완료\n")
    
    for turn in debate_turns:
        print(f"[Turn {turn['turn']}] {turn['phase']}")
        print(f"Speaker: {turn['speaker']} ({turn['type']})")
        if turn.get('target'):
            print(f"Target: {turn['target']}")
        print(f"\n{turn['content'][:200]}...\n")
        print("-" * 80)
    
    # Director 최종 결정
    print("\n" + "=" * 80)
    print("📋 최종 선정된 평가 기준:")
    print("=" * 80)
    
    selected_criteria = final_state.get('selected_criteria', [])
    for idx, criterion in enumerate(selected_criteria, 1):
        print(f"\n{idx}. {criterion.get('name', 'N/A')}")
        print(f"   설명: {criterion.get('description', 'N/A')[:100]}...")
        print(f"   출처: {criterion.get('source_agent', 'N/A')}")
    
    # 결과 저장
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    session_id = final_state['session_id']
    output_file = f"{output_dir}/round1_test_{session_id}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'session_id': session_id,
            'agent_personas': final_state['agent_personas'],
            'debate_turns': debate_turns,
            'selected_criteria': selected_criteria,
            'director_decision': final_state.get('round1_director_decision', {})
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 결과 저장: {output_file}")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
