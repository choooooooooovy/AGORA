"""Base agent class"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model_name: str = "gpt-4o",
        temperature: float = 0.5
    ):
        """
        기본 에이전트 초기화
        
        Args:
            name: 에이전트 이름
            system_prompt: 에이전트 역할을 정의하는 시스템 프롬프트
            model_name: OpenAI 모델 이름
            temperature: 생성 온도 (0-1, 높을수록 창의적)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
    
    def create_prompt(self, user_message: str) -> ChatPromptTemplate:
        """
        시스템 프롬프트와 사용자 메시지로 채팅 프롬프트 생성
        
        Args:
            user_message: 사용자 메시지 내용
            
        Returns:
            시스템 및 사용자 메시지가 포함된 ChatPromptTemplate
        """
        # 중괄호가 있는 문자열을 이스케이프하지 않고 직접 사용
        from langchain_core.messages import SystemMessage, HumanMessage
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message)
        ]
    
    @abstractmethod
    def respond(
        self,
        context: Dict[str, Any],
        round_prompt: str
    ) -> str:
        """
        에이전트의 응답 생성 (추상 메서드 - 하위 클래스에서 구현 필요)
        
        Args:
            context: 사용자 입력 및 대화 히스토리를 포함한 대화 맥락
            round_prompt: 라운드별 특정 프롬프트
            
        Returns:
            에이전트의 응답 문자열
        """
        pass
    
    def format_context(self, context: Dict[str, Any]) -> str:
        """
        에이전트를 위한 맥락 정보 포매팅
        
        Args:
            context: 원본 맥락 딕셔너리
            
        Returns:
            포매팅된 맥락 문자열
        """
        lines = []
        
        # 사용자 성향 (문자열 형태)
        if 'personality' in context and context['personality']:
            lines.append("=== 사용자 성향 ===")
            lines.append(str(context['personality']))
            lines.append("")
        
        # 학습 스타일
        if 'learning_style' in context and context['learning_style']:
            lines.append("=== 학습 스타일 ===")
            lines.append(str(context['learning_style']))
            lines.append("")
        
        # 선호/비선호 과목
        if 'preferred_subjects' in context and context['preferred_subjects']:
            lines.append("=== 선호 과목 ===")
            lines.append(', '.join(context['preferred_subjects']))
            lines.append("")
        
        if 'disliked_subjects' in context and context['disliked_subjects']:
            lines.append("=== 비선호 과목 ===")
            lines.append(', '.join(context['disliked_subjects']))
            lines.append("")
        
        # 자기 평가 능력
        if 'self_ability' in context and context['self_ability']:
            lines.append("=== 자기 평가 능력 ===")
            for skill, level in context['self_ability'].items():
                lines.append(f"- {skill}: {level}/5")
            lines.append("")
        
        # 근거 자료
        if 'evidence' in context and context['evidence']:
            lines.append("=== 근거 자료 ===")
            evidence = context['evidence']
            if evidence.get('grades'):
                lines.append(f"성적: {evidence['grades']}")
            if evidence.get('activities'):
                lines.append(f"활동: {evidence['activities']}")
            if evidence.get('awards'):
                lines.append(f"수상: {evidence['awards']}")
            lines.append("")
        
        # 평가 대상 전공
        if 'alternatives' in context:
            lines.append("=== 평가 대상 전공 ===")
            for alt in context['alternatives']:
                lines.append(f"- {alt}")
            lines.append("")
        
        # 이전 대화 내용
        if 'conversation_history' in context and context['conversation_history']:
            lines.append("=== 이전 대화 내용 ===")
            for entry in context['conversation_history'][-5:]:  # 최근 5개
                lines.append(f"[{entry['agent']}]: {entry['message'][:100]}...")
            lines.append("")
        
        return "\n".join(lines)
