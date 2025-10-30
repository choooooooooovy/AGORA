"""
프론트엔드 연동을 위한 API 예시
FastAPI 또는 Flask에서 사용할 수 있는 구조
"""

from typing import Dict, Any, List
from core.workflow_engine import WorkflowEngine
from models.user_input_schema import UserInput
import json

def run_round1_for_api(user_input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Round 1을 실행하고 프론트엔드에 전달할 수 있는 형태로 반환
    
    Args:
        user_input_dict: 사용자 입력 딕셔너리
        
    Returns:
        {
            "success": bool,
            "session_id": str,
            "conversation": [
                {
                    "turn": 1,
                    "agent": "ValueAgent",
                    "message": "...",
                    "proposals": [...]
                },
                ...
            ],
            "director_decision": {
                "rationale": "...",
                "selected_criteria": [...]
            },
            "final_state": {...}
        }
    """
    try:
        # UserInput 검증
        user_input = UserInput(**user_input_dict)
        
        # WorkflowEngine 초기화
        engine = WorkflowEngine()
        
        # Round 1 실행 (스트리밍 없이)
        final_state = engine.run_round1(user_input, streaming=False)
        
        # 프론트엔드용 응답 구성
        conversation = []
        
        # 각 에이전트의 제안을 턴별로 구성
        for idx, proposal in enumerate(final_state.get('round1_proposals', []), 1):
            conversation.append({
                "turn": idx,
                "agent": proposal['agent_name'],
                "message": proposal['criteria'],
                "timestamp": final_state.get('timestamp', '')
            })
        
        # DirectorAgent 결정 추가
        director_decision = final_state.get('round1_director_decision', {})
        if director_decision:
            conversation.append({
                "turn": len(conversation) + 1,
                "agent": "DirectorAgent",
                "message": director_decision.get('response', ''),
                "selected_criteria": director_decision.get('selected_criteria', []),
                "timestamp": final_state.get('timestamp', '')
            })
        
        return {
            "success": True,
            "session_id": final_state.get('session_id'),
            "round": 1,
            "conversation": conversation,
            "director_decision": {
                "rationale": director_decision.get('response', ''),
                "selected_criteria": final_state.get('selected_criteria', [])
            },
            "metadata": {
                "total_turns": final_state.get('conversation_turns', 0),
                "timestamp": final_state.get('timestamp', '')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# FastAPI 예시
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Round1Request(BaseModel):
    user_input: Dict[str, Any]

@app.post("/api/v1/round1")
async def execute_round1(request: Round1Request):
    result = run_round1_for_api(request.user_input)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/api/v1/round1/{session_id}")
async def get_round1_result(session_id: str):
    # 저장된 상태 파일 읽기
    import json
    try:
        with open(f"output/state_{session_id}_round1.json", "r", encoding="utf-8") as f:
            state = json.load(f)
        
        # 위와 동일한 형식으로 변환
        conversation = []
        for idx, proposal in enumerate(state.get('round1_proposals', []), 1):
            conversation.append({
                "turn": idx,
                "agent": proposal['agent_name'],
                "message": proposal['criteria']
            })
        
        return {
            "success": True,
            "session_id": session_id,
            "conversation": conversation,
            "selected_criteria": state.get('selected_criteria', [])
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
"""

# React/Vue 프론트엔드 예시 (pseudocode)
"""
// Round 1 실행
async function executeRound1(userInput) {
    const response = await fetch('/api/v1/round1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: userInput })
    });
    
    const data = await response.json();
    
    // 대화 내용을 순차적으로 표시
    for (const turn of data.conversation) {
        displayMessage({
            agent: turn.agent,
            message: turn.message,
            turn: turn.turn
        });
        
        // 애니메이션 효과를 위해 약간의 지연
        await sleep(500);
    }
    
    // 최종 선정 기준 표시
    displayFinalCriteria(data.director_decision.selected_criteria);
    
    return data.session_id;
}

function displayMessage({ agent, message, turn }) {
    const chatDiv = document.getElementById('chat-container');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${agent.toLowerCase()}`;
    messageElement.innerHTML = `
        <div class="agent-name">${agent}</div>
        <div class="agent-message">${formatMessage(message)}</div>
    `;
    
    chatDiv.appendChild(messageElement);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}
"""

if __name__ == "__main__":
    # 테스트
    with open("data/user_inputs/sample_template.json", "r", encoding="utf-8") as f:
        user_input = json.load(f)
    
    result = run_round1_for_api(user_input)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
