"""Data models and schemas for the prioritization framework - 간소화 버전"""

import json
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

from models.user_input_schema import UserInput
from models.state import ConversationState


def load_user_input(filepath: str) -> Dict[str, Any]:
    """
    사용자 입력 JSON 파일 로드 및 검증
    
    Args:
        filepath: JSON 파일 경로
        
    Returns:
        검증된 사용자 입력 딕셔너리
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Pydantic 검증
    try:
        user_input = UserInput(**data)
        return user_input.model_dump()
    except ValidationError as e:
        print(f"[ERROR] 입력 데이터 검증 실패:")
        for error in e.errors():
            print(f"  - {error['loc']}: {error['msg']}")
        raise


__all__ = [
    "UserInput",
    "ConversationState",
    "load_user_input"
]
