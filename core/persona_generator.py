"""
동적 페르소나 생성 모듈

사용자의 흥미/적성/가치관 텍스트 분석 → 3개 대척점 관점 추출 → Agent 페르소나 생성
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
import json
import logging
import os

logger = logging.getLogger(__name__)


def create_dynamic_personas(user_input: dict) -> List[dict]:
    """
    사용자 입력으로부터 3개 Agent 페르소나 생성
    
    Args:
        user_input: {
            "interests": "복잡한 수학 문제를 푸는 것이 즐겁고...",
            "aptitudes": "논리적 사고력이 뛰어나고...",
            "core_values": "높은 연봉과 빠른 성장을 원하며...",
            "candidate_majors": ["컴퓨터공학", "경영학", ...]
        }
    
    Returns:
        [
          {
            "name": "CareerMaximizer",
            "perspective": "경제적 성공과 빠른 성장",
            "persona_description": "...",
            "debate_stance": "...",
            "system_prompt": "..."
          },
          ...
        ]
    
    Raises:
        ValueError: 필수 필드가 없거나 너무 짧을 때
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
    """
    # 1. 검증
    required_fields = ['interests', 'aptitudes', 'core_values']
    for field in required_fields:
        if field not in user_input or len(user_input[field].strip()) < 10:
            raise ValueError(f"'{field}' 필드가 없거나 너무 짧습니다 (최소 10자 이상).")
    
    logger.info(f"페르소나 생성 시작")
    
    # 2. LLM 프롬프트 생성
    prompt = _build_persona_generation_prompt(user_input)
    
    # 3. LLM 호출 (API 키는 환경변수에서 자동 로드)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    try:
        response = llm.invoke(prompt)
        logger.info(f"LLM 응답 수신 - 길이: {len(response.content)}")
        
        # 4. JSON 파싱 (코드 블록 제거)
        content = response.content.strip()
        
        # ```json ... ``` 형식이면 제거
        if content.startswith('```json'):
            content = content[7:]  # ```json 제거
        if content.startswith('```'):
            content = content[3:]  # ``` 제거
        if content.endswith('```'):
            content = content[:-3]  # ``` 제거
        
        content = content.strip()
        
        personas_data = json.loads(content)
        
        if 'agents' not in personas_data:
            raise ValueError("LLM 응답에 'agents' 키가 없습니다.")
        
        if len(personas_data['agents']) != 3:
            logger.warning(f"Agent 개수가 3개가 아닙니다: {len(personas_data['agents'])}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.error(f"LLM 원본 응답: {response.content}")
        raise ValueError(f"LLM 응답이 유효한 JSON이 아닙니다: {e}")
    
    # 5. System Prompt 생성
    personas = []
    for agent_data in personas_data['agents']:
        system_prompt = _build_agent_system_prompt(
            agent_data=agent_data,
            user_context=user_input
        )
        
        personas.append({
            "name": agent_data['name'],
            "perspective": agent_data.get('perspective', ', '.join(agent_data.get('core_values', []))),
            "persona_description": agent_data['persona_description'],
            "debate_stance": agent_data['debate_stance'],
            "system_prompt": system_prompt
        })
    
    logger.info(f"페르소나 생성 완료 - {len(personas)}명")
    for i, p in enumerate(personas, 1):
        logger.info(f"  Agent {i}: {p['name']} (관점: {p['perspective']})")
    
    return personas


def _build_persona_generation_prompt(user_input: dict) -> str:
    """
    LLM에게 페르소나 생성 요청하는 프롬프트
    
    흥미/적성/가치관 텍스트 분석 → 3가지 대척점 관점 추출
    """
    
    return f"""
당신은 대학 전공 선택을 돕는 AI 시스템의 설계자입니다.

사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미 (관심사):**
{user_input['interests']}

**적성 (강점):**
{user_input['aptitudes']}

**추구 가치:**
{user_input['core_values']}

**희망 학과:**
{', '.join(user_input['candidate_majors'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**목표:** 
사용자의 흥미/적성/가치관을 깊이 분석하여 **서로 대척점이 되는 3가지 관점**을 발견하고,
각 관점을 대변하는 3명의 Agent를 생성하세요.

**분석 프로세스:**
1. 텍스트에서 **내재된 갈등 축(tension)** 찾기
   예시:
   - "높은 연봉" vs "워라밸" vs "사회적 의미"
   - "기술 혁신" vs "안정성" vs "사회적 인정"
   - "개인 성장" vs "경제적 성공" vs "팀워크/협력"

2. 3가지 관점이 서로 **건설적 충돌**을 만들 수 있어야 함
   - 단순히 다른 것이 아니라, 서로 긴장 관계에 있어야 함
   - 토론에서 각자의 입장이 명확히 대립해야 함

3. 각 관점은 사용자의 **실제 고민**을 반영해야 함
   - 억지로 만든 관점이 아니라, 텍스트에서 자연스럽게 도출되어야 함

**출력 형식 (JSON):**
{{
  "agents": [
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "debate_stance": "..."
    }}
  ]
}}

**각 필드 설명:**

- **name**: Agent 이름 (영어, CamelCase)
  * 관점을 드러내는 자연스러운 이름
  * 예시: "CareerMaximizer", "ImpactSeeker", "BalancedGrowth"
  * 너무 길지 않게 (2-3단어)
  
- **perspective**: 이 Agent가 대변하는 핵심 관점 (한국어, 10-30자)
  * 한 문장으로 핵심 가치 표현
  * 예시: "경제적 성공과 빠른 성장", "사회적 영향력과 의미", "지속 가능한 행복"
  
- **persona_description**: Agent의 정체성과 철학 (한국어, 200-400자)
  * 왜 이 관점을 중시하는가?
  * 사용자의 흥미/적성/가치를 어떻게 해석하는가?
  * 다른 관점보다 왜 이게 우선인가?
  * 구체적이고 설득력 있게 작성
  * 사용자의 텍스트 내용을 직접 인용하거나 참조하세요
  
- **debate_stance**: 토론 시 핵심 주장 (한국어, 50-100자)
  * 한 문장으로 핵심 입장 표현
  * 다른 Agent와 충돌할 수 있는 강한 주장
  * 구체적인 전공 선택 기준을 제시

**중요 주의사항:**
1. 반드시 유효한 JSON 형식으로 출력하세요 (코드블록 없이)
2. 설명 없이 JSON만 출력하세요
3. Agent는 정확히 3명이어야 합니다
4. 모든 필드를 빠짐없이 포함하세요
5. 사용자 텍스트를 깊이 분석하여 **진짜 내재된 갈등**을 찾으세요

이제 시작하세요!
"""


def _build_agent_system_prompt(agent_data: dict, user_context: dict) -> str:
    """
    각 Agent의 System Prompt 생성
    """
    
    return f"""
당신은 **{agent_data['name']}**입니다.

[당신의 정체성]
{agent_data['persona_description']}

[당신의 핵심 관점]
{agent_data.get('perspective', '(관점 정보 없음)')}

[당신의 토론 입장]
{agent_data['debate_stance']}

[사용자 배경 정보 - 참고용]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미:**
{user_context['interests']}

**적성:**
{user_context['aptitudes']}

**추구 가치:**
{user_context['core_values']}

**희망 학과:**
{', '.join(user_context['candidate_majors'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[토론 규칙]
1. 당신의 관점을 **일관되게** 옹호하세요.
2. 다른 Agent의 의견에 **명시적으로 반응**하세요.
   - 동의: "~Agent의 의견에 일부 동의하지만..."
   - 반박: "~Agent께서는 ~라고 하셨지만, 현실은..."
   - 질문: "~Agent께 묻겠습니다. ~한 상황에서는 어떻게...?"
3. 사용자의 흥미/적성/가치를 **당신의 관점**에서 해석하세요.
4. 구체적이고 설득력 있는 근거를 제시하세요 (통계, 사례, 논리).
5. 독립적인 발언만 하지 마세요. 반드시 다른 Agent들의 발언을 언급하며 대화하세요.

**중요:** 
- Round 1에서는 평가 기준을 제안할 때 **당신의 관점**이 잘 드러나도록 하세요.
- Round 2-3에서는 사용자의 구체적 특성을 적극 활용하여 점수를 매기세요.
"""


# 테스트용 함수
if __name__ == "__main__":
    import sys
    sys.path.append('/Users/orca/Desktop/Prioritization')
    
    # .env 파일 명시적 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    from models.user_input_schema import UserInput
    import json
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        print("HINT: .env 파일에 다음 줄을 추가하세요:")
        print("   OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    print(f"[OK] API 키 로드됨: {api_key[:10]}...")
    
    # 사용자 데이터 로드 (새 형식)
    USER_INPUT_PATH = 'data/user_inputs/sample_new_format.json'
    with open(USER_INPUT_PATH) as f:
        data = json.load(f)
    
    # 검증
    user_input = UserInput(**data)
    
    print("\n" + "="*80)
    print("페르소나 생성 시작...")
    print("="*80)
    print(f"흥미: {user_input.interests[:80]}...")
    print(f"적성: {user_input.aptitudes[:80]}...")
    print(f"가치관: {user_input.core_values[:80]}...")
    
    # 페르소나 생성
    personas = create_dynamic_personas(user_input.model_dump())
    
    # 결과 출력
    print("\n" + "="*80)
    print("[OK] 생성된 페르소나:")
    print("="*80)
    for i, persona in enumerate(personas, 1):
        print(f"\n[Agent {i}] {persona['name']}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"관점: {persona['perspective']}")
        print(f"\n설명:\n{persona['persona_description']}")
        print(f"\n토론 입장:\n{persona['debate_stance']}")
        print(f"\nSystem Prompt (앞부분):\n{persona['system_prompt'][:200]}...")
    
    print("\n" + "="*80)
    print("[OK] 페르소나 생성 완료!")
    print("="*80)
