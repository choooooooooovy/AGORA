# 사용자 입력 필드 참조 위치 정리

## 📁 데이터 파일

**단일 파일 사용**:
- `data/user_inputs/current_user.json` (유일한 사용자 입력 파일)
- ~~`data/user_inputs/sample_new_format.json`~~ (삭제됨 - 중복)

---

## 📋 사용자 입력 필드 (3개 자유 텍스트)

### 1. `interests` (흥미)
**정의**: 사용자의 흥미, 관심사, 좋아하는 활동 등을 자유롭게 서술 (최소 10자)

**참조 위치**:

#### 스키마 정의
- `models/user_input_schema.py` (라인 35-39)
  - 필드 정의 및 validation

#### 페르소나 생성
- `core/persona_generator.py` (라인 45, 128, 236, 297)
  - **라인 45**: 필수 필드 검증
  - **라인 128**: LLM 프롬프트에 포함 (페르소나 생성용)
  - **라인 236**: Agent 시스템 프롬프트에 포함
  - **라인 297**: 테스트 출력

#### Round 1-3 토론 프롬프트
- `workflows/round1_criteria.py` (라인 103, 380)
  - **라인 103**: Agent 제안 프롬프트에 사용자 정보 제공
  - **라인 380**: 추가 Agent 프롬프트

- `workflows/round2_ahp.py` (라인 199)
  - AHP 쌍대비교 시 사용자 특성 제공

- `workflows/round3_scoring.py` (라인 156)
  - Decision Matrix 점수 평가 시 사용자 특성 제공

---

### 2. `aptitudes` (적성)
**정의**: 사용자의 적성, 강점, 잘하는 것들을 자유롭게 서술 (최소 10자)

**참조 위치**:

#### 스키마 정의
- `models/user_input_schema.py` (라인 41-45)
  - 필드 정의 및 validation

#### 페르소나 생성
- `core/persona_generator.py` (라인 45, 131, 239, 298)
  - **라인 45**: 필수 필드 검증
  - **라인 131**: LLM 프롬프트에 포함 (페르소나 생성용)
  - **라인 239**: Agent 시스템 프롬프트에 포함
  - **라인 298**: 테스트 출력

#### Round 1-3 토론 프롬프트
- `workflows/round1_criteria.py` (라인 106, 383)
  - Agent 제안 프롬프트에 사용자 정보 제공

- `workflows/round2_ahp.py` (라인 202)
  - AHP 쌍대비교 시 사용자 특성 제공

- `workflows/round3_scoring.py` (라인 159)
  - Decision Matrix 점수 평가 시 사용자 특성 제공

---

### 3. `core_values` (추구 가치)
**정의**: 사용자가 추구하는 가치, 중요하게 생각하는 것들을 자유롭게 서술 (최소 10자)

**참조 위치**:

#### 스키마 정의
- `models/user_input_schema.py` (라인 47-51)
  - 필드 정의 및 validation

#### 페르소나 생성 (핵심!)
- `core/persona_generator.py` (라인 45, 134, 242, 299)
  - **라인 45**: 필수 필드 검증
  - **라인 134**: LLM 프롬프트에 포함 (대척점 관점 추출의 핵심 소스!)
  - **라인 242**: Agent 시스템 프롬프트에 포함
  - **라인 299**: 테스트 출력

#### Round 1-3 토론 프롬프트
- `workflows/round1_criteria.py` (라인 109, 386)
  - Agent 제안 프롬프트에 사용자 정보 제공

- `workflows/round2_ahp.py` (라인 205)
  - AHP 쌍대비교 시 사용자 특성 제공

- `workflows/round3_scoring.py` (라인 162)
  - Decision Matrix 점수 평가 시 사용자 특성 제공

---

## 🔍 핵심 흐름

### 1단계: 페르소나 생성 (`core/persona_generator.py`)
```python
# 라인 45-49: 필수 필드 검증
required_fields = ['interests', 'aptitudes', 'core_values']
for field in required_fields:
    if field not in user_input or len(user_input[field].strip()) < 10:
        raise ValueError(f"'{field}' 필드가 없거나 너무 짧습니다")

# 라인 128-134: LLM에게 3가지 텍스트 전달
**흥미:**
{user_input['interests']}

**적성:**
{user_input['aptitudes']}

**추구 가치:**
{user_input['core_values']}  # ← 대척점 추출의 핵심!
```

### 2단계: Round 1-3 토론 (`workflows/round*.py`)
```python
# 각 Agent에게 사용자 정보 제공
사용자 정보:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**흥미:**
{user_input.get('interests', 'N/A')}

**적성:**
{user_input.get('aptitudes', 'N/A')}

**추구 가치:**
{user_input.get('core_values', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ 정리

1. **데이터 파일**: `current_user.json` 하나만 사용
2. **3가지 자유 텍스트**는 모두 10자 이상 필수
3. **`core_values`가 가장 중요**: LLM이 여기서 대척점 관점을 추출
4. **모든 Round에서 참조**: Agent들이 사용자 맥락을 이해하고 토론함

