"""에이전트 팩토리: 시스템 프롬프트를 로드하여 에이전트 인스턴스 생성"""

import yaml
from pathlib import Path
from typing import Dict, Any
from agents import ValueAgent, FitAgent, MarketAgent, DirectorAgent


class AgentFactory:
    """에이전트 생성 팩토리 클래스"""
    
    def __init__(
        self,
        system_prompts_path: str = None,
        model_name: str = "gpt-4o"
    ):
        """
        AgentFactory 초기화
        
        Args:
            system_prompts_path: system_prompts.yaml 파일 경로
            model_name: 사용할 OpenAI 모델 이름
        """
        self.model_name = model_name
        
        # 기본 경로 설정
        if system_prompts_path is None:
            system_prompts_path = Path(__file__).parent.parent / "templates" / "system_prompts.yaml"
        
        # 시스템 프롬프트 로드
        self.system_prompts = self._load_system_prompts(system_prompts_path)
    
    def _load_system_prompts(self, path: str) -> Dict[str, Any]:
        """
        시스템 프롬프트 YAML 파일 로드
        
        Args:
            path: YAML 파일 경로
            
        Returns:
            시스템 프롬프트 딕셔너리
        """
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def create_value_agent(self, temperature: float = 0.5) -> ValueAgent:
        """
        ValueAgent 생성
        
        Args:
            temperature: 생성 온도
            
        Returns:
            초기화된 ValueAgent 인스턴스
        """
        prompt_config = self.system_prompts['value_agent']
        
        # 전체 시스템 프롬프트 조합
        system_prompt = f"{prompt_config['role']}\n\n"
        system_prompt += f"## 가이드라인\n{prompt_config['guidelines']}\n\n"
        system_prompt += f"## 맥락 활용\n{prompt_config['context_usage']}"
        
        return ValueAgent(
            system_prompt=system_prompt,
            model_name=self.model_name,
            temperature=temperature
        )
    
    def create_fit_agent(self, temperature: float = 0.5) -> FitAgent:
        """
        FitAgent 생성
        
        Args:
            temperature: 생성 온도
            
        Returns:
            초기화된 FitAgent 인스턴스
        """
        prompt_config = self.system_prompts['fit_agent']
        
        system_prompt = f"{prompt_config['role']}\n\n"
        system_prompt += f"## 가이드라인\n{prompt_config['guidelines']}\n\n"
        system_prompt += f"## 맥락 활용\n{prompt_config['context_usage']}"
        
        return FitAgent(
            system_prompt=system_prompt,
            model_name=self.model_name,
            temperature=temperature
        )
    
    def create_market_agent(self, temperature: float = 0.5) -> MarketAgent:
        """
        MarketAgent 생성
        
        Args:
            temperature: 생성 온도
            
        Returns:
            초기화된 MarketAgent 인스턴스
        """
        prompt_config = self.system_prompts['market_agent']
        
        system_prompt = f"{prompt_config['role']}\n\n"
        system_prompt += f"## 가이드라인\n{prompt_config['guidelines']}\n\n"
        system_prompt += f"## 맥락 활용\n{prompt_config['context_usage']}"
        
        return MarketAgent(
            system_prompt=system_prompt,
            model_name=self.model_name,
            temperature=temperature
        )
    
    def create_director_agent(self, temperature: float = 0.0) -> DirectorAgent:
        """
        DirectorAgent 생성
        
        Args:
            temperature: 생성 온도 (기본값 0.0 - 일관성 중시)
            
        Returns:
            초기화된 DirectorAgent 인스턴스
        """
        prompt_config = self.system_prompts['director_agent']
        
        system_prompt = f"{prompt_config['role']}\n\n"
        system_prompt += f"## 가이드라인\n{prompt_config['guidelines']}\n\n"
        system_prompt += f"## 의사결정 프로세스\n{prompt_config['decision_process']}\n\n"
        system_prompt += f"## 응답 형식\n{prompt_config['response_format']}"
        
        return DirectorAgent(
            system_prompt=system_prompt,
            model_name=self.model_name,
            temperature=temperature
        )
    
    def create_all_agents(
        self,
        agent_temperature: float = 0.5,
        director_temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        모든 에이전트 생성
        
        Args:
            agent_temperature: 전문가 에이전트들의 온도
            director_temperature: DirectorAgent의 온도
            
        Returns:
            에이전트 딕셔너리
        """
        return {
            'value_agent': self.create_value_agent(agent_temperature),
            'fit_agent': self.create_fit_agent(agent_temperature),
            'market_agent': self.create_market_agent(agent_temperature),
            'director_agent': self.create_director_agent(director_temperature)
        }
