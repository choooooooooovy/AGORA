"""
AGORA Backend API Server
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from datetime import datetime
import os

from config import Config
from models.user_input_schema import UserInput
from core.persona_generator import create_dynamic_personas
from workflows.round1_criteria import run_round1_debate
from workflows.round2_ahp import run_round2_debate
from workflows.round3_scoring import run_round3_debate
from workflows.round4_topsis import calculate_topsis_ranking
from utils.datetime_utils import get_kst_timestamp, get_kst_now
from workflows.report_generator import generate_final_report, save_report

# 설정 검증
Config.validate()

app = FastAPI(
    title="AGORA API",
    description="AI Multi-Agent Decision Making System",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class UserInputRequest(BaseModel):
    """사용자 입력 요청"""
    interests: str = Field(..., description="흥미")
    aptitudes: str = Field(..., description="적성")
    core_values: str = Field(..., description="핵심 가치")
    candidate_majors: List[str] = Field(..., min_length=3, description="후보 전공 리스트 (최소 3개)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "interests": "인공지능, 데이터 분석, 문제 해결",
                "aptitudes": "논리적 사고, 프로그래밍",
                "core_values": "혁신, 사회 기여",
                "candidate_majors": ["컴퓨터공학", "수리데이터사이언스", "인공지능"]
            }
        }


class UserInputResponse(BaseModel):
    """사용자 입력 응답"""
    success: bool
    session_id: str
    message: str
    personas: Optional[List[Dict[str, Any]]] = None


class RoundRequest(BaseModel):
    """라운드 실행 요청"""
    session_id: str = Field(..., description="세션 ID")


class RoundResponse(BaseModel):
    """라운드 실행 응답"""
    success: bool
    session_id: str
    round: int
    message: str
    data: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """최종 보고서 응답"""
    success: bool
    session_id: str
    report: Optional[Dict[str, Any]] = None


# ==================== Helper Functions ====================

def generate_session_id() -> str:
    """세션 ID 생성"""
    timestamp = int(get_kst_now().timestamp() * 1000)
    import random
    import string
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{timestamp}-{random_suffix}"


def save_user_input(session_id: str, user_input: UserInputRequest) -> Path:
    """사용자 입력 저장"""
    Config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    user_input_data = {
        "session_id": session_id,
        "timestamp": get_kst_timestamp(),
        "interests": user_input.interests,
        "aptitudes": user_input.aptitudes,
        "core_values": user_input.core_values,
        "candidate_majors": user_input.candidate_majors,
        "settings": {
            "max_criteria": Config.MAX_CRITERIA,
            "cr_threshold": Config.MAX_CR,
            "cr_max_retries": Config.MAX_AHP_RETRIES,
            "enable_streaming": False
        }
    }
    
    file_path = Config.INPUT_DIR / f"{session_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_input_data, f, ensure_ascii=False, indent=2)
    
    return file_path


def load_session_data(session_id: str) -> Dict[str, Any]:
    """세션 데이터 로드"""
    file_path = Config.INPUT_DIR / f"{session_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_round_output(session_id: str, round_num: int) -> Dict[str, Any]:
    """라운드 출력 로드"""
    file_path = Config.OUTPUT_DIR / f"round{round_num}_{session_id}.json"
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Round {round_num} output not found. Please run round {round_num} first."
        )
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "AGORA API",
        "version": "1.0.0",
        "timestamp": get_kst_timestamp()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_configured": bool(Config.OPENAI_API_KEY),
        "timestamp": get_kst_timestamp()
    }


@app.post("/api/user-input", response_model=UserInputResponse)
async def create_user_input(user_input: UserInputRequest):
    """
    사용자 입력 저장 및 페르소나 생성
    """
    try:
        # 세션 ID 생성
        session_id = generate_session_id()
        
        # 사용자 입력 저장
        save_user_input(session_id, user_input)
        
        # 페르소나 생성
        user_input_dict = {
            "interests": user_input.interests,
            "aptitudes": user_input.aptitudes,
            "core_values": user_input.core_values,
            "candidate_majors": user_input.candidate_majors
        }
        
        personas = create_dynamic_personas(user_input_dict)
        personas_data = {"personas": personas}
        
        # 페르소나 저장
        personas_file = Config.OUTPUT_DIR / f"personas_{session_id}.json"
        with open(personas_file, "w", encoding="utf-8") as f:
            json.dump(personas_data, f, ensure_ascii=False, indent=2)
        
        return UserInputResponse(
            success=True,
            session_id=session_id,
            message="User input saved and personas generated successfully",
            personas=personas_data.get("personas", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/round/1", response_model=RoundResponse)
async def execute_round1(request: RoundRequest):
    """
    Round 1: 평가 기준 도출 (Criteria Generation)
    """
    try:
        session_data = load_session_data(request.session_id)
        
        # 페르소나 로드
        personas_file = Config.OUTPUT_DIR / f"personas_{request.session_id}.json"
        with open(personas_file, "r", encoding="utf-8") as f:
            personas_data = json.load(f)
        
        # Round 1 state 준비
        initial_state = {
            'user_input': session_data,
            'agent_personas': personas_data["personas"],
            'alternatives': session_data["candidate_majors"],
            'agent_weights': [1.0, 1.0, 1.0],
            'max_criteria': session_data["settings"]["max_criteria"]
        }
        
        # Round 1 실행
        final_state = run_round1_debate(initial_state)
        
        # Director decision 찾기 (마지막 final_decision 턴)
        director_decision = None
        for turn in reversed(final_state.get("round1_debate_turns", [])):
            if turn.get("type") == "final_decision":
                director_decision = turn
                break
        
        # 결과 저장
        output_data = {
            "session_id": request.session_id,
            "timestamp": get_kst_timestamp(),
            "round1_debate_turns": final_state.get("round1_debate_turns", []),
            "round1_director_decision": director_decision,
            "final_criteria": final_state.get("selected_criteria", [])
        }
        
        output_file = Config.OUTPUT_DIR / f"round1_{request.session_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return RoundResponse(
            success=True,
            session_id=request.session_id,
            round=1,
            message="Round 1 completed successfully",
            data=output_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/round/2", response_model=RoundResponse)
async def execute_round2(request: RoundRequest):
    """
    Round 2: AHP 가중치 계산 (AHP Weighting)
    """
    try:
        session_data = load_session_data(request.session_id)
        round1_data = load_round_output(request.session_id, 1)
        
        # 페르소나 로드
        personas_file = Config.OUTPUT_DIR / f"personas_{request.session_id}.json"
        with open(personas_file, "r", encoding="utf-8") as f:
            personas_data = json.load(f)
        
        # Round 2 state 준비
        round2_state = {
            'user_input': session_data,
            'agent_personas': personas_data["personas"],
            'selected_criteria': round1_data["final_criteria"],
            'alternatives': session_data["candidate_majors"],
            'max_ahp_retries': session_data["settings"]["cr_max_retries"],
            'cr_threshold': session_data["settings"]["cr_threshold"]
        }
        
        # Round 2 실행
        final_state = run_round2_debate(round2_state)
        
        # Director decision 찾기
        director_decision = None
        for turn in reversed(final_state.get("round2_debate_turns", [])):
            if turn.get("type") == "final_decision":
                director_decision = turn
                break
        
        # 결과 저장
        output_data = {
            "session_id": request.session_id,
            "timestamp": get_kst_timestamp(),
            "round2_debate_turns": final_state.get("round2_debate_turns", []),
            "round2_director_decision": director_decision,
            "criteria_weights": final_state.get("criteria_weights", {}),
            "consistency_ratio": final_state.get("consistency_ratio", 0.0)
        }
        
        output_file = Config.OUTPUT_DIR / f"round2_{request.session_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return RoundResponse(
            success=True,
            session_id=request.session_id,
            round=2,
            message="Round 2 completed successfully",
            data=output_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/round/3", response_model=RoundResponse)
async def execute_round3(request: RoundRequest):
    """
    Round 3: 대안 점수 매기기 (Scoring Alternatives)
    """
    try:
        session_data = load_session_data(request.session_id)
        round1_data = load_round_output(request.session_id, 1)
        
        # 페르소나 로드
        personas_file = Config.OUTPUT_DIR / f"personas_{request.session_id}.json"
        with open(personas_file, "r", encoding="utf-8") as f:
            personas_data = json.load(f)
        
        # Round 3 state 준비
        round3_state = {
            'user_input': session_data,
            'agent_personas': personas_data["personas"],
            'selected_criteria': round1_data["final_criteria"],
            'alternatives': session_data["candidate_majors"]
        }
        
        # Round 3 실행
        final_state = run_round3_debate(round3_state)
        
        # Director decision 찾기
        director_decision = None
        for turn in reversed(final_state.get("round3_debate_turns", [])):
            if turn.get("type") == "final_decision":
                director_decision = turn
                break
        
        # 결과 저장
        output_data = {
            "session_id": request.session_id,
            "timestamp": get_kst_timestamp(),
            "round3_debate_turns": final_state.get("round3_debate_turns", []),
            "round3_director_decision": director_decision,
            "decision_matrix": final_state.get("decision_matrix", {})
        }
        
        output_file = Config.OUTPUT_DIR / f"round3_{request.session_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return RoundResponse(
            success=True,
            session_id=request.session_id,
            round=3,
            message="Round 3 completed successfully",
            data=output_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/round/4", response_model=RoundResponse)
async def execute_round4(request: RoundRequest):
    """
    Round 4: TOPSIS 최종 순위 (Final Ranking)
    """
    try:
        # 모든 필요한 이전 라운드 데이터 로드
        session_data = load_session_data(request.session_id)
        round1_data = load_round_output(request.session_id, 1)
        round2_data = load_round_output(request.session_id, 2)
        round3_data = load_round_output(request.session_id, 3)
        
        # Round 4 state 준비 (TOPSIS 계산에 필요한 모든 데이터)
        round4_state = {
            'session_id': request.session_id,
            'user_input': session_data,  # candidate_majors 포함
            'selected_criteria': round1_data["final_criteria"],  # 선정된 기준들
            'criteria_weights': round2_data["criteria_weights"],
            'decision_matrix': round3_data["decision_matrix"]
        }
        
        # Round 4 실행
        final_state = calculate_topsis_ranking(round4_state)
        
        # TOPSIS result에서 ranking 추출
        topsis_result = final_state.get('topsis_result', {})
        ranking_list = topsis_result.get('ranking', [])
        
        # 결과 저장
        output_data = {
            "session_id": request.session_id,
            "timestamp": get_kst_timestamp(),
            "final_ranking": ranking_list,
            "topsis_details": {
                "ideal_solution": topsis_result.get('ideal_solution', {}),
                "anti_ideal_solution": topsis_result.get('anti_ideal_solution', {})
            }
        }
        
        output_file = Config.OUTPUT_DIR / f"round4_{request.session_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return RoundResponse(
            success=True,
            session_id=request.session_id,
            round=4,
            message="Round 4 completed successfully",
            data=output_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str):
    """
    최종 보고서 조회
    """
    try:
        # 모든 라운드 데이터 로드
        session_data = load_session_data(session_id)
        
        personas_file = Config.OUTPUT_DIR / f"personas_{session_id}.json"
        with open(personas_file, "r", encoding="utf-8") as f:
            personas_data = json.load(f)
        
        round1_data = load_round_output(session_id, 1)
        round2_data = load_round_output(session_id, 2)
        round3_data = load_round_output(session_id, 3)
        round4_data = load_round_output(session_id, 4)
        
        # 보고서 생성
        report = generate_final_report(
            session_id=session_id,
            user_input=session_data,
            personas=personas_data["personas"],
            round1_result=round1_data,
            round2_result=round2_data,
            round3_result=round3_data,
            round4_result=round4_data
        )
        
        # 보고서 저장
        save_report(report, session_id, Config.OUTPUT_DIR)
        
        return ReportResponse(
            success=True,
            session_id=session_id,
            report=report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
