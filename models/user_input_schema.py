"""
간소화된 사용자 입력 스키마 (User Input Schema)

동적 페르소나 생성을 위한 최소한의 사용자 정보만 수집
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SessionSettings(BaseModel):
    """세션 설정"""
    max_criteria: int = Field(default=5, ge=3, le=10, description="Maximum number of criteria")
    cr_threshold: float = Field(default=0.10, ge=0.0, le=0.15, description="Consistency Ratio threshold for AHP")
    cr_max_retries: int = Field(default=3, ge=1, le=5, description="Maximum CR retry attempts")
    enable_streaming: bool = Field(default=False, description="Enable streaming output")


class UserInput(BaseModel):
    """
    간소화된 사용자 입력 스키마
    
    동적 페르소나 생성을 위해 필요한 최소한의 정보만 수집:
    1. MBTI
    2. 강점/약점
    3. 좋아하는/싫어하는 과목
    4. 잘하는/못하는 과목
    5. 핵심 가치 (3개 이상)
    6. 희망 학과 (3~5개)
    """
    
    # 기본 정보
    session_id: Optional[str] = Field(default=None, description="Unique session identifier (auto-generated if not provided)")
    timestamp: Optional[str] = Field(default=None, description="Session timestamp")
    
    # 사용자 성향
    mbti: str = Field(..., description="MBTI personality type (e.g., ENFP)")
    
    strengths: List[str] = Field(..., min_length=1, description="User's strengths")
    weaknesses: List[str] = Field(..., min_length=1, description="User's weaknesses")
    
    # 과목 선호도
    favorite_subjects: List[str] = Field(..., min_length=1, description="Subjects the user likes")
    disliked_subjects: List[str] = Field(..., min_length=1, description="Subjects the user dislikes")
    
    good_at_subjects: List[str] = Field(..., min_length=1, description="Subjects the user excels at")
    bad_at_subjects: List[str] = Field(..., min_length=1, description="Subjects the user struggles with")
    
    # 핵심 가치 (동적 페르소나 생성의 핵심)
    core_values: List[str] = Field(
        ..., 
        min_length=3,
        description="Core values for major selection (minimum 3). Examples: '적성 일치', '높은 급여', '미래 전망', '워라밸', '사회적 기여'"
    )
    
    # 희망 학과
    candidate_majors: List[str] = Field(
        ...,
        min_length=3,
        description="Candidate majors to evaluate (minimum 3 required)"
    )
    
    # 세션 설정
    settings: SessionSettings = Field(default_factory=SessionSettings, description="Session settings")
    
    @field_validator('core_values')
    @classmethod
    def validate_core_values(cls, v):
        """핵심 가치는 최소 3개 이상 필요"""
        if len(v) < 3:
            raise ValueError("최소 3개 이상의 핵심 가치를 입력해주세요.")
        return v
    
    @field_validator('candidate_majors')
    @classmethod
    def validate_majors(cls, v):
        """희망 학과는 최소 3개 이상"""
        if len(v) < 3:
            raise ValueError("희망 학과는 최소 3개 이상 입력해주세요.")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mbti": "ENFP",
                "strengths": ["창의적 사고", "팀워크", "문제 해결"],
                "weaknesses": ["집중력 부족", "계획성 부족"],
                "favorite_subjects": ["디자인", "수학"],
                "disliked_subjects": ["물리", "화학"],
                "good_at_subjects": ["수학", "디자인", "영어"],
                "bad_at_subjects": ["물리", "체육"],
                "core_values": ["적성 일치", "높은 급여", "미래 전망", "워라밸", "사회적 기여"],
                "candidate_majors": ["컴퓨터공학", "산업디자인", "경영학"],
                "settings": {
                    "max_criteria": 5,
                    "cr_threshold": 0.10,
                    "cr_max_retries": 3,
                    "enable_streaming": False
                }
            }
        }
