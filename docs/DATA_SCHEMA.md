# Data Schema Documentation

## Overview

이 문서는 Prioritization Framework의 데이터 스키마 구조를 설명합니다.

---

## 1. User Input Schema (data/user_inputs/sample_template_new.json)

### UserInput
전체 사용자 입력을 담는 메인 스키마입니다.

```json
{
  "mbti": "<16가지 MBTI 유형 중 하나>",
  "strengths": ["<강점1>", "<강점2>", "..."],
  "weaknesses": ["<약점1>", "<약점2>", "..."],
  "favorite_subjects": ["<선호 과목1>", "<선호 과목2>", "..."],
  "disliked_subjects": ["<비선호 과목1>", "<비선호 과목2>", "..."],
  "good_at_subjects": ["<잘하는 과목1>", "<잘하는 과목2>", "..."],
  "bad_at_subjects": ["<못하는 과목1>", "<못하는 과목2>", "..."],
  "core_values": ["<가치관1>", "<가치관2>", "..."],
  "candidate_majors": ["<전공1>", "<전공2>", "..."],
  "settings": {
    "max_criteria": 5,
    "cr_threshold": 0.10,
    "cr_max_retries": 3,
    "enable_streaming": false
  }
}
```

### 필드 설명

#### 사용자 특성
- **mbti**: MBTI 성격 유형 (16가지 중 하나: ISTJ, ISFJ, INFJ, INTJ, ISTP, ISFP, INFP, INTP, ESTP, ESFP, ENFP, ENTP, ESTJ, ESFJ, ENFJ, ENTJ)
- **strengths**: 사용자의 강점 리스트 (자유 형식)
- **weaknesses**: 사용자의 약점 리스트 (자유 형식)
- **favorite_subjects**: 선호하는 과목 리스트 (자유 형식)
- **disliked_subjects**: 싫어하는 과목 리스트 (자유 형식)
- **good_at_subjects**: 잘하는 과목 리스트 (자유 형식)
- **bad_at_subjects**: 못하는 과목 리스트 (자유 형식)
- **core_values**: 사용자의 핵심 가치관 리스트 (자유 형식, Agent 생성 시 분배됨)

#### 평가 대상
- **candidate_majors**: 평가할 전공 리스트 (최소 2개, 자유 형식)

#### 세션 설정
- **settings.max_criteria**: 최대 기준 개수 (기본 5)
- **settings.cr_threshold**: AHP Consistency Ratio 임계값 (기본 0.10)
- **settings.cr_max_retries**: CR 재시도 최대 횟수 (기본 3)
- **settings.enable_streaming**: 스트리밍 출력 활성화 여부 (기본 false)

---

## 2. Agent Personas (자동 생성)

워크플로우 엔진이 사용자의 `core_values`를 기반으로 자동 생성합니다.

### AgentPersona 구조

```python
{
  "name": "<Agent 고유 이름>",  # 자동 생성된 Agent 이름
  "core_values": ["<가치1>", "<가치2>"],  # 담당 가치 (1-2개)
  "persona_description": "<페르소나 설명>",  # 성격과 관점 설명
  "debate_stance": "<토론 입장>",  # 토론에서의 주장 방향
  "system_prompt": "<LLM 프롬프트>"  # Agent의 시스템 프롬프트
}
```

### 생성 규칙
- 사용자의 `core_values`를 **3개 Agent**에게 균등 분배
- 각 Agent는 **1-2개**의 가치를 담당
- 사용자 특성(MBTI, 강점, 약점)을 반영한 페르소나 자동 생성
- Agent 이름은 담당 가치의 특성을 반영하여 자동 생성

---

## 3. Conversation State (models/state.py)

### ConversationState
LangGraph 워크플로우의 메인 상태입니다.

#### 기본 정보
- **user_input**: 사용자 입력 전체 (dict)
- **session_id**: 세션 고유 ID
- **alternatives**: 평가 대상 전공 리스트 (user_input의 candidate_majors)
- **agent_personas**: 생성된 Agent 페르소나 리스트

#### Round 1: 기준 선정 (13-turn Debate)
- **round1_debate_turns**: 13턴 토론 내역 (List[dict])
  - turn, phase, speaker, type, content, timestamp
- **selected_criteria**: 최종 선정된 기준 리스트 (List[dict])
  - name, description, type, source_agent, reasoning

#### Round 2: AHP 쌍대비교 (13-turn Debate)
- **round2_debate_turns**: 13턴 토론 내역 (List[dict])
  - turn, phase, speaker, type, content, comparison_matrix, timestamp
- **comparison_matrix**: 최종 비교 행렬 (Dict[str, float])
  - key: "기준A vs 기준B", value: Saaty 척도 (1.0-9.0, 0.5 단위)
- **criteria_weights**: AHP 가중치 (Dict[str, float])
- **consistency_ratio**: CR 값 (float)
- **eigenvalue_max**: 최대 고유값 (float)
- **round2_director_decision**: Director 최종 결정 내역

#### Round 3: Decision Matrix (13-turn Debate)
- **round3_debate_turns**: 13턴 토론 내역 (List[dict])
  - turn, phase, speaker, type, content, decision_matrix, timestamp
- **decision_matrix**: 최종 Decision Matrix (Dict[str, Dict[str, float]])
  - key1: 전공명, key2: 기준명, value: 점수 (1.0-9.0, 0.5 단위)
- **round3_director_decision**: Director 최종 결정 내역
  - decision_matrix, reasoning

#### Round 4: TOPSIS 순위 계산
- **normalized_matrix**: 정규화 행렬
- **weighted_matrix**: 가중 행렬
- **ideal_solution**: 이상해 (A+)
- **anti_ideal_solution**: 반이상해 (A-)
- **topsis_results**: TOPSIS 결과
- **final_ranking**: 최종 순위

---

## 4. Debate Turn Structure

### 13-Turn Debate System
모든 Round(1, 2, 3)는 동일한 13턴 구조를 사용합니다.

#### Phase 1-3: Agent 주도권 (각 4턴 × 3 = 12턴)
```python
{
  "turn": 1,
  "phase": "Phase 1: PassionDriven 주도권",
  "speaker": "PassionDriven",
  "type": "proposal",  # 제안
  "content": "...",
  "timestamp": "2025-11-03T01:32:15.123456"
}

{
  "turn": 2,
  "phase": "Phase 1: PassionDriven 주도권",
  "speaker": "PragmaticEarner",
  "type": "critique",  # 반박
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 3,
  "phase": "Phase 1: PassionDriven 주도권",
  "speaker": "SocialContributor",
  "type": "critique",  # 반박
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 4,
  "phase": "Phase 1: PassionDriven 주도권",
  "speaker": "PassionDriven",
  "type": "defense",  # 재반박
  "target": ["PragmaticEarner", "SocialContributor"],
  "content": "...",
  "timestamp": "..."
}
```

#### Phase 4: Director 최종 결정 (1턴)
```python
{
  "turn": 13,
  "phase": "Phase 4: Director 최종 결정",
  "speaker": "Director",
  "type": "final_decision",
  "content": "...",
  "timestamp": "..."
}
```

### Round별 추가 필드

**Round 1**: selected_criteria (최종 선정 기준)
**Round 2**: comparison_matrix (비교 행렬)
**Round 3**: decision_matrix (Decision Matrix)

---

## 5. Output Files

### Round 1 Output
```
output/round1_test_{session_id}.json
```
- user_input
- agent_personas
- round1_debate_turns
- selected_criteria

### Round 2 Output  
```
output/round2_test_{session_id}.json
```
- user_input
- agent_personas
- selected_criteria
- round2_debate_turns
- comparison_matrix
- criteria_weights
- consistency_ratio
- eigenvalue_max
- round2_director_decision

### Round 3 Output
```
output/round3_test_{session_id}.json
```
- user_input
- agent_personas
- selected_criteria
- criteria_weights
- round3_debate_turns
- decision_matrix
- round3_director_decision

---

## 6. Data Flow

```
[User Input JSON]
    ↓
[WorkflowEngine.initialize_state()]
    ↓
[Agent Personas 자동 생성]
    ↓
┌─────────────────────────────────────────┐
│ Round 1: Criteria Selection (13 turns) │
│ - 각 Agent가 기준 제안                   │
│ - Director가 최종 5개 선정               │
│ → selected_criteria                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 2: AHP Comparison (13 turns)     │
│ - 10개 쌍 비교 (nC2, n=5)               │
│ - Director가 최종 비교 행렬 결정         │
│ - AHP 가중치 계산                       │
│ → criteria_weights, CR                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 3: Decision Matrix (13 turns)    │
│ - 전공 × 기준 모든 조합 점수 부여        │
│ - Director가 최종 매트릭스 결정          │
│ → decision_matrix                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 4: TOPSIS Ranking                │
│ - 정규화, 가중치 적용                    │
│ - 이상해/반이상해 계산                   │
│ - 최종 순위 도출                        │
│ → final_ranking                         │
└─────────────────────────────────────────┘
```

---

## 7. Validation Rules

### User Input Validation
- `mbti`: 16가지 MBTI 유형 중 하나
- `candidate_majors`: 최소 2개 이상
- `core_values`: 최소 1개 이상 (Agent 생성에 필요)
- `settings.max_criteria`: 3-10 범위
- `settings.cr_threshold`: 0.05-0.20 범위

### Round 1 Validation
- `selected_criteria`: 정확히 max_criteria 개수

### Round 2 Validation
- `comparison_matrix`: nC2 개 쌍 비교 (n = len(selected_criteria))
- 모든 비교값: 0.5 단위 (1.0, 1.5, 2.0, ..., 9.0)
- `consistency_ratio`: ≤ cr_threshold

### Round 3 Validation
- `decision_matrix`: 모든 (전공 × 기준) 조합 존재
- 모든 점수: 0.5 단위 (1.0, 1.5, 2.0, ..., 9.0)
- 점수 다양성: 같은 점수 3회 이하 권장

### Round 4 Validation
- `final_ranking`: 순위 중복 없음 (1, 2, 3, ...)
- `closeness_coefficient`: 0.0-1.0 범위
- 가중치 합: 1.0

---

## 8. Score Guides

### Round 2: AHP Saaty Scale (1-9, 0.5 단위)

**[1.0 - 2.5] 거의 동등 ~ 약간 중요**
- 1.0: 동등 - 두 기준이 거의 같은 수준
- 1.5: 거의 동등 - 매우 미세한 차이
- 2.0: 약간 중요 - 조금 더 중요
- 2.5: 약간 더 중요 - 눈에 띄기 시작

**[3.0 - 5.0] 중요 ~ 매우 중요**
- 3.0: 중요 - 명확히 더 중요
- 3.5: 상당히 중요 - 확실한 차이
- 4.0: 매우 중요 - 크게 더 중요
- 4.5: 아주 중요 - 큰 차이
- 5.0: 필수적 - 핵심적 차이

**[5.5 - 9.0] 극도로 중요 ~ 절대적**
- 5.5-7.0: 극도로 중요
- 7.5-9.0: 절대적으로 중요 (드물게 사용)

### Round 3: Decision Matrix Scale (1-9, 0.5 단위)

**[1.0 - 3.0] 부적합 구간**
- 1.0-2.0: 매우 부적합 ~ 부적합
- 2.5-3.0: 약간 부적합 ~ 다소 부적합

**[3.5 - 5.5] 보통 구간**
- 3.5-4.0: 보통 이하 ~ 보통
- 4.5-5.0: 보통 이상 ~ 적합
- 5.5: 상당히 적합

**[6.0 - 9.0] 적합 구간**
- 6.0-7.0: 매우 적합 ~ 탁월하게 적합
- 7.5-8.5: 매우 탁월 ~ 거의 완벽
- 9.0: 완벽하게 적합 (드물게 사용)

**점수 분포 가이드:**
- 대부분: 3-7점 범위
- 8-9점: 예외적인 경우만 (5% 이내)
- 1-2점: 명백히 부적합한 경우만 (5% 이내)
