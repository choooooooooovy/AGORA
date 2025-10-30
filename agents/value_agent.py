"""가치 중심 에이전트"""

from typing import Dict, Any
from .base_agent import BaseAgent


class ValueAgent(BaseAgent):
    """가치와 의미에 집중하는 에이전트"""
    
    def __init__(
        self,
        system_prompt: str,
        model_name: str = "gpt-4o",
        temperature: float = 0.5
    ):
        """ValueAgent 초기화"""
        super().__init__(
            name="ValueAgent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature
        )
    
    def respond(
        self,
        context: Dict[str, Any],
        round_prompt: str
    ) -> str:
        """
        가치와 의미에 초점을 맞춘 응답 생성
        
        Args:
            context: 대화 맥락
            round_prompt: 라운드별 프롬프트
            
        Returns:
            에이전트의 응답
        """
        # 맥락 포매팅
        formatted_context = self.format_context(context)
        
        # 전체 사용자 메시지 생성
        user_message = f"{formatted_context}\n\n{round_prompt}"
        
        # 메시지 리스트 생성 및 LLM 호출
        messages = self.create_prompt(user_message)
        
        response = self.llm.invoke(messages)
        
        return response.content
