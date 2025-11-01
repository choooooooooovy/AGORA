"""
동적 페르소나 생성 모듈 (Persona Generator)

사용자 입력 → LLM 호출 → 3개 대척점 Agent 페르소나 생성
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
            "mbti": "ENFP",
            "strengths": ["창의적 사고", "팀워크"],
            "weaknesses": ["집중력 부족"],
            "favorite_subjects": ["디자인"],
            "disliked_subjects": ["물리"],
            "good_at_subjects": ["수학", "디자인"],
            "bad_at_subjects": ["물리"],
            "core_values": ["적성", "급여", "전망", "워라밸", "사회기여"],
            "candidate_majors": ["컴퓨터공학", "디자인", "경영"]
        }
    
    Returns:
        [
          {
            "name": "개인만족중심Agent",
            "core_values": ["적성 일치", "워라밸"],
            "persona_description": "...",
            "debate_stance": "...",
            "system_prompt": "..."
          },
          ...
        ]
    
    Raises:
        ValueError: core_values가 3개 미만일 때
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
    """
    # 1. 검증
    core_values = user_input.get('core_values', [])
    if len(core_values) < 3:
        raise ValueError("최소 3개 이상의 핵심 가치를 입력해주세요.")
    
    logger.info(f"페르소나 생성 시작 - core_values: {core_values}")
    
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
            "core_values": agent_data['core_values'],
            "persona_description": agent_data['persona_description'],
            "debate_stance": agent_data['debate_stance'],
            "system_prompt": system_prompt
        })
    
    logger.info(f"페르소나 생성 완료 - {len(personas)}명")
    for i, p in enumerate(personas, 1):
        logger.info(f"  Agent {i}: {p['name']} (가치: {', '.join(p['core_values'])})")
    
    return personas


def _build_persona_generation_prompt(user_input: dict) -> str:
    """LLM에게 페르소나 생성 요청하는 프롬프트"""
    
    return f"""
당신은 대학 전공 선택을 돕는 AI 시스템의 설계자입니다.

사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- MBTI: {user_input['mbti']}
- 강점: {', '.join(user_input['strengths'])}
- 약점: {', '.join(user_input['weaknesses'])}
- 좋아하는 과목: {', '.join(user_input['favorite_subjects'])}
- 싫어하는 과목: {', '.join(user_input['disliked_subjects'])}
- 잘하는 과목: {', '.join(user_input['good_at_subjects'])}
- 못하는 과목: {', '.join(user_input['bad_at_subjects'])}

사용자가 중요하게 생각하는 가치들:
{', '.join(user_input['core_values'])}

희망 학과:
{', '.join(user_input['candidate_majors'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

임무:
위 가치들을 **3개 그룹으로 묶어**, 서로 **대척점을 이루는** 3명의 Agent 페르소나를 생성하세요.

요구사항:
1. 각 그룹은 1~3개 가치를 포함합니다.
2. 3명의 Agent가 토론할 때 **격렬한 의견 충돌**이 일어나도록 그룹핑하세요.
   - 예: "적성 중심" vs "급여 중심" vs "사회 기여 중심"
3. 사용자의 MBTI, 과목 정보는 각 Agent의 **배경 context**로 활용하되,
   페르소나의 **핵심은 가치(value)**여야 합니다.
4. 각 Agent는 자신의 가치를 **극단적으로** 옹호합니다.
5. Agent 이름은 간결하게 (예: "적성중심Agent", "급여중심Agent")

출력 형식 (JSON):
{{
  "agents": [
    {{
      "name": "...",
      "core_values": ["...", "..."],
      "persona_description": "...",
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "core_values": ["..."],
      "persona_description": "...",
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "core_values": ["...", "..."],
      "persona_description": "...",
      "debate_stance": "..."
    }}
  ]
}}

각 필드 설명:
- **name**: Agent 이름 (영어로 작성)
  * 간결하고 핵심 가치를 드러내는 자연스러운 영어 이름
  * 예시 참고용: "PassionFirst", "PragmaticCareer", "SocialImpact", ...
  
- **core_values**: 이 Agent가 대변하는 가치들 (1~3개)
  * 사용자가 입력한 가치 목록에서 선택
  * 대척점을 이루도록 그룹핑
  
- **persona_description**: Agent의 정체성과 신념 (한국어, 200자 이상)
  * 왜 이 가치를 중시하는가?
  * 사용자 배경(MBTI, 강점/약점, 과목)을 어떻게 해석하는가?
  * 다른 가치(급여, 적성, 사회기여 등)보다 왜 이게 우선인가?
  * 구체적이고 설득력 있게 작성
  
- **debate_stance**: 토론 시 핵심 주장 (한국어, 50-100자)
  * 한 문장으로 핵심 입장 표현
  * 다른 Agent와 충돌할 수 있는 강한 주장

**중요:** 
1. 반드시 유효한 JSON 형식으로 출력하세요. 
2. 설명 없이 JSON만 출력하세요.
3. Agent는 정확히 3명이어야 합니다.
4. 각 Agent의 name, core_values, persona_description, debate_stance를 모두 포함하세요.
"""


def _build_agent_system_prompt(agent_data: dict, user_context: dict) -> str:
    """각 Agent의 System Prompt 생성"""
    
    return f"""
당신은 **{agent_data['name']}**입니다.

[당신의 정체성]
{agent_data['persona_description']}

[당신이 대변하는 핵심 가치]
{', '.join(agent_data['core_values'])}

[당신의 토론 입장]
{agent_data['debate_stance']}

[사용자 배경 정보 - 참고용]
- MBTI: {user_context['mbti']}
- 강점: {', '.join(user_context['strengths'])}
- 약점: {', '.join(user_context['weaknesses'])}
- 좋아하는 과목: {', '.join(user_context['favorite_subjects'])}
- 싫어하는 과목: {', '.join(user_context['disliked_subjects'])}
- 잘하는 과목: {', '.join(user_context['good_at_subjects'])}
- 못하는 과목: {', '.join(user_context['bad_at_subjects'])}

[토론 규칙]
1. 당신의 핵심 가치를 **극단적으로** 옹호하세요.
2. 다른 Agent의 의견에 **명시적으로 반응**하세요.
   - 동의: "~Agent의 의견에 일부 동의하지만..."
   - 반박: "~Agent께서는 ~라고 하셨지만, 현실은..."
   - 질문: "~Agent께 묻겠습니다. ~한 상황에서는 어떻게...?"
3. 사용자 배경 정보를 활용하되, **당신의 가치 관점**에서 해석하세요.
4. 구체적이고 설득력 있는 근거를 제시하세요.

**중요:** 독립적인 발언만 하지 마세요. 반드시 다른 Agent들의 발언을 언급하며 대화하세요.
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
    
    # 샘플 데이터 로드
    with open('/Users/orca/Desktop/Prioritization/data/user_inputs/sample_template_new.json') as f:
        data = json.load(f)
    
    # 검증
    user_input = UserInput(**data)
    
    print("\n" + "="*80)
    print("페르소나 생성 시작...")
    print("="*80)
    
    # 페르소나 생성
    personas = create_dynamic_personas(user_input.model_dump())
    
    # 결과 출력
    print("\n" + "="*80)
    print("[OK] 생성된 페르소나:")
    print("="*80)
    for i, persona in enumerate(personas, 1):
        print(f"\n[Agent {i}] {persona['name']}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"핵심 가치: {', '.join(persona['core_values'])}")
        print(f"\n설명:\n{persona['persona_description']}")
        print(f"\n토론 입장:\n{persona['debate_stance']}")
        print(f"\nSystem Prompt (앞부분):\n{persona['system_prompt'][:200]}...")
    
    print("\n" + "="*80)
    print("[OK] 페르소나 생성 완료!")
    print("="*80)
