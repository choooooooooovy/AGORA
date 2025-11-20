"""Persona Generator - 빠른 페르소나 생성 (Round 1 토론 제외)"""

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
    print("Usage: python generate_personas.py <session_id>")
    sys.exit(1)

session_id = sys.argv[1]

# 사용자 데이터 로드 (session_id 기반)
USER_INPUT_PATH = f'data/user_inputs/{session_id}.json'

if not os.path.exists(USER_INPUT_PATH):
    print(f"Error: User input file not found: {USER_INPUT_PATH}")
    sys.exit(1)

with open(USER_INPUT_PATH, 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# UserInput 검증
user_input = UserInput(**test_data)

print("=" * 80)
print("[Persona Generation] 에이전트 페르소나 생성")
print("=" * 80)

# WorkflowEngine 초기화
engine = WorkflowEngine(
    model_name="gpt-4o",
    agent_temperature=0.7,
    director_temperature=0.0,
    max_criteria=5
)

# 초기 상태 생성 (페르소나 포함)
print("\n[1단계] 페르소나 생성 중...")
initial_state = engine.initialize_state(user_input.model_dump())

# 페르소나만 추출하여 저장
personas_output = {
    "session_id": session_id,
    "user_input": initial_state['user_input'],
    "agent_personas": initial_state['agent_personas']
}

# 출력 디렉토리 생성
os.makedirs('output', exist_ok=True)
output_path = f'output/personas_{session_id}.json'

# JSON 파일로 저장
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(personas_output, f, ensure_ascii=False, indent=2)

print(f"\n✅ 페르소나 생성 완료: {output_path}")
print(f"✅ 생성된 에이전트 수: {len(initial_state['agent_personas'])}")

for persona in initial_state['agent_personas']:
    print(f"  - {persona['name']}: {persona['perspective']}")
