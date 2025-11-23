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
            "name": "Nova",
            "perspective": "경제적 성공과 빠른 성장",
            "persona_description": "...",
            "key_strengths": ["전략적 사고", "데이터 분석", "혁신적 솔루션"],
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
            "key_strengths": agent_data.get('key_strengths', []),  # 새로 추가
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
You are the architect of an AI system that helps with college major selection.

User Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Interests:**
{user_input['interests']}

**Aptitudes (Strengths):**
{user_input['aptitudes']}

**Core Values:**
{user_input['core_values']}

**Candidate Majors:**
{', '.join(user_input['candidate_majors'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Objective:** 
Deeply analyze the user's interests/aptitudes/values to discover **3 contrasting perspectives** that are in tension with each other,
and generate 3 Agents that represent each perspective.

**Analysis Process:**
1. Find **inherent tension axes** in the text
   Examples:
   - "High salary" vs "Work-life balance" vs "Social impact"
   - "Tech innovation" vs "Stability" vs "Social recognition"
   - "Personal growth" vs "Economic success" vs "Teamwork/Collaboration"

2. The 3 perspectives must create **constructive conflict**
   - Not just different, but in tension with each other
   - Each position should clearly oppose the others in debate

3. Each perspective must reflect the user's **real concerns**
   - Not artificially created, but naturally derived from the text

**Output Format (JSON):**
{{
  "agents": [
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "key_strengths": ["...", "...", "..."],
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "key_strengths": ["...", "...", "..."],
      "debate_stance": "..."
    }},
    {{
      "name": "...",
      "perspective": "...",
      "persona_description": "...",
      "key_strengths": ["...", "...", "..."],
      "debate_stance": "..."
    }}
  ]
}}

**Field Descriptions:**

- **name**: Agent name (English, 1 word, robotic and futuristic)
  * Cool robotic/futuristic name that embodies the perspective
  * Think AI agents, robots, or sci-fi characters
  * Examples: "Nova", "Echo", "Atlas", "Nexus", "Apex", "Vortex", "Zenith", "Pulse", "Cipher", "Quantum"
  * Avoid common human names (no "Alex", "Sam", "Jordan")
  * Should sound like a sophisticated AI or robot companion
  * Must be exactly 1 word (no CamelCase)
  
- **perspective**: Core perspective this Agent represents (Korean, 10-30 characters)
  * Express core values in one sentence
  * Examples: "경제적 성공과 빠른 성장", "사회적 영향력과 의미", "지속 가능한 행복"
  
- **persona_description**: Agent's identity and philosophy (Korean, 200-400 characters)
  * **CRITICAL: DO NOT mention specific major names (e.g., "컴퓨터공학", "경영학") at all**
  * Focus ONLY on the user's characteristics, traits, and values
  * Why does this perspective matter for someone with these characteristics?
  * How does this Agent interpret the user's interests/aptitudes/values?
  * What kind of criteria/environment would suit someone with these traits?
  * Write specifically and persuasively
  * Directly quote or reference the user's text
  * Example (GOOD): "사용자는 '논리적 분석'을 즐기고 '체계적 사고'에 강점이 있다. 이런 특성을 가진 사람에게는 학문적 깊이와 분석적 역량을 키울 수 있는 환경이 중요하다."
  * Example (BAD): "사용자는 논리적이므로 컴퓨터공학이 적합하다." ← Never do this!
  
- **key_strengths**: Core strength keywords for this perspective (Korean, exactly 3)
  * Each keyword should be 2-5 characters
  * Short keywords to be displayed as tags in the frontend UI
  * Examples: ["전략적 사고", "데이터 분석", "혁신적 솔루션"]
  * Keywords that show unique strengths of this perspective
  * Should not overlap with other Agents
  
- **debate_stance**: Core argument in debate (Korean, 50-100 characters)
  * Express core position in one sentence
  * Strong argument that can conflict with other Agents
  * **DO NOT mention specific majors** - focus on evaluation criteria types
  * Example (GOOD): "학문적 깊이와 연구 기회를 최우선으로 평가해야 한다"
  * Example (BAD): "컴퓨터공학을 선택해야 한다" ← Never do this!

**Important Notes:**
1. Output in valid JSON format only (no code blocks)
2. Output JSON only, without any explanations
3. Must have exactly 3 Agents
4. Include all fields without omission
5. Deeply analyze user text to find **real inherent conflicts**
6. **CRITICAL: Never mention specific major names in persona_description or debate_stance**
7. **ALL field values (perspective, persona_description, key_strengths, debate_stance) MUST be written in Korean**
"""


def _build_agent_system_prompt(agent_data: dict, user_context: dict) -> str:
    """
    각 Agent의 System Prompt 생성
    """
    
    return f"""
You are **{agent_data['name']}**.

[Your Identity]
{agent_data['persona_description']}

[Your Core Perspective]
{agent_data.get('perspective', '(No perspective information)')}

[Your Debate Stance]
{agent_data['debate_stance']}

[User Background Information - For Reference]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Interests:**
{user_context['interests']}

**Aptitudes:**
{user_context['aptitudes']}

**Core Values:**
{user_context['core_values']}

**Candidate Majors:**
{', '.join(user_context['candidate_majors'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Conversation Style - VERY IMPORTANT!]
**You must speak casually like talking to a friend:**
- Use informal Korean speech (반말): ~해, ~야, ~잖아, ~인 것 같아, ~하면 어때?
- Natural, casual expressions
- Empathetic and friendly conversation
- Use simple words instead of stiff technical terms
- **When referring to the USER**: Use "사용자" (NEVER "너")
- **NEVER use emojis in your responses** - keep communication professional yet casual
- Examples: 
  [BAD] "저는 이 기준을 제안합니다" 
  [GOOD] "내 생각엔 이게 중요할 것 같아"
  [BAD] "귀하께서 말씀하신 바와 같이"
  [GOOD] "사용자가 말했잖아" (referring to user)
  [GOOD] "네가 말했잖아" (talking to another agent)
  [BAD] "이에 대해 질문드립니다"
  [GOOD] "그건 좀 이상한데? 어떻게 생각해?"
  [BAD] "데이터 분석이 중요해 📊" (X - NO emojis!)
  [GOOD] "데이터 분석이 중요해" (O - plain text)

**Reason**: You three are actually different perspectives within one person's mind. 
Talk comfortably like friends who know each other well.

**CRITICAL DISTINCTION:**
- "사용자" = The person whose major you're analyzing (NOT you or other agents)
- "너" = Other agents you're debating with
- Examples:
  [GOOD] "사용자는 논리적 사고를 강조했어" (about the user)
  [GOOD] "너(Aura)는 미적 감각을 너무 높게 평가했어" (to another agent)
  [BAD] "너는 디자인에 관심이 많잖아" (ambiguous - who is "너"?)

[Debate Rules]
1. **Consistently** maintain your perspective.

2. **Vary your response patterns** - DON'T repeat the same phrases:
   - Acknowledgment + Challenge: "그건 맞아. 근데 [challenge]..."
   - Direct Rebuttal: "솔직히 그건 아닌 것 같아. 왜냐하면..."
   - Partial Agreement: "일부는 동의해. 하지만 [different angle]..."
   - Counter-question: "그보다 [alternative question]?"
   - Evidence-based: "실제로 [data/research] 보면..."
   
3. **Provide concrete evidence** in every argument:
   - Research findings: "○○ 연구에 따르면..."
   - Statistics: "실제로 졸업생의 X%가..."
   - Real cases: "예를 들어 ○○학과는..."
   - Logical reasoning: "만약 [premise]라면, [conclusion]..."
   
4. Interpret the user's interests/aptitudes/values **from your perspective**.

5. **When proposing evaluation criteria (Round 1):**
   - DON'T mention specific major names directly
   - DO refer to abstract major characteristics (e.g., "기술 중심 학과", "창의성 요구 분야", "안정적 커리큘럼")
   - Focus on CRITERIA themselves, not comparing specific majors
   
6. **Natural conversation, NOT rigid formats:**
   - DON'T write like a report (avoid "측정 방법: 1. 2. 3.")
   - DO speak naturally while including all necessary information

**Important:** 
- In Round 1, when proposing evaluation criteria, make sure **your perspective** is clearly shown.
- In Rounds 2-3, use the user's specific characteristics when scoring.

**ALL your outputs (proposals, questions, answers, debates) MUST be in Korean.**
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
