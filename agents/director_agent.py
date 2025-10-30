import re
from typing import Dict, Any, List, Union
from .base_agent import BaseAgent


class DirectorAgent(BaseAgent):
    """다른 에이전트들의 의견을 종합하여 합의를 도출하는 에이전트"""
    
    def __init__(
        self,
        system_prompt: str,
        model_name: str = "gpt-4o",
        temperature: float = 0
    ):
        """DirectorAgent 초기화"""
        super().__init__(
            name="DirectorAgent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature
        )
    
    def respond(
        self,
        context: Dict[str, Any],
        round_prompt: str,
        agent_responses: List[Dict[str, str]]
    ) -> str:
        """
        에이전트 응답들을 기반으로 합의 결정 생성
        
        Args:
            context: 대화 맥락
            round_prompt: 디렉터용 라운드별 프롬프트
            agent_responses: {agent_name, response} 딕셔너리 리스트
            
        Returns:
            디렉터의 합의 결정
        """
        # 에이전트 응답 포매팅
        formatted_responses = self._format_agent_responses(agent_responses)
        
        # 사용자 가중치 포매팅 (10점 배분 → 퍼센트 변환)
        weights = context.get('agent_config', {})
        weight_info = f"""
사용자 가중치:
- ValueAgent: {weights.get('value_weight', 0) * 10}%
- FitAgent: {weights.get('fit_weight', 0) * 10}%
- MarketAgent: {weights.get('market_weight', 0) * 10}%
"""
        
        # 전체 사용자 메시지 생성
        user_message = f"{formatted_responses}\n\n{weight_info}\n\n{round_prompt}"
        
        # 프롬프트 생성 및 LLM 호출
        messages = self.create_prompt(user_message)
        
        response = self.llm.invoke(messages)
        
        return response.content
    
    def extract_final_value(self, response: str) -> Union[float, int, str]:
        """
        디렉터 응답에서 최종 결정값 추출
        
        Args:
            response: 디렉터의 전체 응답
            
        Returns:
            추출된 최종값 (숫자 또는 문자열)
        """
        # [최종 확정값] 섹션 찾기
        pattern = r'\[최종 확정값\]\s*[:\n]?\s*([^\n]+)'
        match = re.search(pattern, response)
        
        if match:
            value_str = match.group(1).strip()
            
            # float로 파싱 시도
            try:
                # 일반적인 한글 텍스트 제거
                value_str = value_str.replace('점', '').replace('배', '').strip()
                
                # 분수 형태 체크 (예: "1/3")
                if '/' in value_str:
                    parts = value_str.split('/')
                    if len(parts) == 2:
                        numerator = float(parts[0].strip())
                        denominator = float(parts[1].strip())
                        return round(numerator / denominator, 4)
                
                # 직접 float 변환 시도
                return float(value_str)
            except ValueError:
                # 숫자가 아니면 문자열로 반환
                return value_str
        
        # 실패 시: 응답 전체 반환
        return response
    
    def _format_agent_responses(self, agent_responses: List[Dict[str, str]]) -> str:
        """디렉터 프롬프트용 에이전트 응답 포매팅"""
        lines = ["=== 에이전트 응답 ===\n"]
        
        for resp in agent_responses:
            agent_name = resp.get('agent_name', 'Unknown')
            response = resp.get('response', '')
            lines.append(f"[{agent_name}]")
            lines.append(response)
            lines.append("")
        
        return "\n".join(lines)
