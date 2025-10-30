"""설정 파일: 환경 변수 및 기본 설정"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """애플리케이션 설정"""
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 에이전트 설정
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.5"))
    DIRECTOR_TEMPERATURE = float(os.getenv("DIRECTOR_TEMPERATURE", "0.0"))
    
    # AHP 설정
    MAX_CRITERIA = int(os.getenv("MAX_CRITERIA", "5"))
    MAX_CR = float(os.getenv("MAX_CR", "0.10"))
    MAX_AHP_RETRIES = int(os.getenv("MAX_AHP_RETRIES", "3"))
    
    # 프로젝트 경로
    PROJECT_ROOT = Path(__file__).parent
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    DATA_DIR = PROJECT_ROOT / "data"
    INPUT_DIR = PROJECT_ROOT / "data" / "user_inputs"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    
    # 디버그 모드
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in .env file.")
        
        # 출력 디렉토리 생성
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_summary(cls) -> str:
        """설정 요약"""
        return f"""
Configuration Summary:
- OpenAI Model: {cls.OPENAI_MODEL}
- Agent Temperature: {cls.AGENT_TEMPERATURE}
- Director Temperature: {cls.DIRECTOR_TEMPERATURE}
- Max Criteria: {cls.MAX_CRITERIA}
- Max CR: {cls.MAX_CR}
- Debug Mode: {cls.DEBUG}
"""
