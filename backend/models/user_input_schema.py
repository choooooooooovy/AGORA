"""
간소화된 사용자 입력 스키마 (User Input Schema)

3가지 자유 텍스트 기반 페르소나 생성
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SessionSettings(BaseModel):
    """세션 설정"""
    max_criteria: int = Field(default=4, ge=3, le=10, description="Maximum number of criteria")
    cr_threshold: float = Field(default=0.10, ge=0.0, le=0.15, description="Consistency Ratio threshold for AHP")
    cr_max_retries: int = Field(default=3, ge=1, le=5, description="Maximum CR retry attempts")
    enable_streaming: bool = Field(default=False, description="Enable streaming output")


class UserInput(BaseModel):
    """
    간소화된 사용자 입력 스키마
    
    3가지 자유 텍스트로 사용자의 맥락을 풍부하게 전달:
    1. 흥미 (interests): 무엇에 관심이 있고 즐거움을 느끼는가?
    2. 적성 (aptitudes): 무엇을 잘하고 강점이 있는가?
    3. 추구 가치 (core_values): 어떤 가치를 중요하게 생각하는가?
    4. 희망 학과 (candidate_majors): 평가할 학과 리스트
    """
    
    # 기본 정보
    session_id: Optional[str] = Field(default=None, description="Unique session identifier (auto-generated if not provided)")
    timestamp: Optional[str] = Field(default=None, description="Session timestamp")
    
    # 사용자 특성 (자유 텍스트)
    interests: str = Field(
        ..., 
        min_length=10,
        description="사용자의 흥미, 관심사, 좋아하는 활동 등을 자유롭게 서술 (최소 10자)"
    )
    
    aptitudes: str = Field(
        ..., 
        min_length=10,
        description="사용자의 적성, 강점, 잘하는 것들을 자유롭게 서술 (최소 10자)"
    )
    
    core_values: str = Field(
        ..., 
        min_length=10,
        description="사용자가 추구하는 가치, 중요하게 생각하는 것들을 자유롭게 서술 (최소 10자)"
    )
    
    # 희망 학과
    candidate_majors: List[str] = Field(
        ...,
        min_length=2,
        description="Candidate majors to evaluate (minimum 2 majors)"
    )
    
    # 세션 설정
    settings: SessionSettings = Field(default_factory=SessionSettings, description="Session settings")
    
    @field_validator('interests', 'aptitudes', 'core_values')
    @classmethod
    def validate_text_length(cls, v):
        """자유 텍스트는 최소 10자 이상"""
        if len(v.strip()) < 10:
            raise ValueError("최소 10자 이상 입력해주세요.")
        return v.strip()
    
    @field_validator('candidate_majors')
    @classmethod
    def validate_majors(cls, v):
        """희망 학과는 최소 2개 이상"""
        if len(v) < 2:
            raise ValueError("희망 학과는 최소 2개 이상 입력해주세요.")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "interests": "복잡한 수학 문제를 푸는 과정이 즐겁고, 프로그래밍으로 알고리즘을 구현하는 것에 흥미가 있습니다. 최신 기술 트렌드를 따라가며 새로운 도구를 배우는 것을 좋아합니다.",
                "aptitudes": "논리적 사고력이 뛰어나고 코딩 능력이 우수합니다. 문제 해결 과정에서 창의적인 접근을 잘하며, 수학 경시대회에서 입상한 경험이 있습니다.",
                "core_values": "높은 연봉과 빠른 커리어 성장을 원하며, 글로벌 기업에서 일하고 싶습니다. 하지만 워라밸도 중요하게 생각하고, 사회적으로 의미 있는 일을 하고 싶습니다.",
                "candidate_majors": ["컴퓨터공학", "전기전자공학", "산업공학", "경영학"],
                "settings": {
                    "max_criteria": 4,
                    "cr_threshold": 0.10,
                    "cr_max_retries": 3,
                    "enable_streaming": False
                }
            }
        }
