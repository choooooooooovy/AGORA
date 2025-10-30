# Data Schema Documentation

## Overview

이 문서는 Prioritization Framework의 데이터 스키마 구조를 설명합니다.

## 1. User Input Schema (models/user_input_schema.py)

### UserInput
전체 사용자 입력을 담는 메인 스키마입니다.

```python
{
    "session_id": str,           # 고유 세션 ID
    "timestamp": str,            # 타임스탬프
    "context": UserContext,      # 사용자 컨텍스트
    "agent_config": AgentConfig, # 에이전트 가중치 설정
    "alternatives": AlternativeConfig,  # 평가할 대안들
    "settings": SessionSettings  # 세션 설정
}
```

### UserContext
에이전트가 참고할 사용자 정보입니다.

- personality: 성격 설명 (BFI-2-S 기반)
- learning_style: 선호 학습 방식
- evaluation_style: 선호 평가 방식
- preferred_subjects: 선호 과목 리스트
- disliked_subjects: 비선호 과목 리스트
- self_ability: 자가 평가 능력 (SelfAbility)
- evidence: 능력 근거 (Evidence)

### AgentConfig
에이전트 발언권 설정 (총합 10점)

- value_weight: ValueAgent 가중치 (0-10)
- fit_weight: FitAgent 가중치 (0-10)
- market_weight: MarketAgent 가중치 (0-10)

### SelfAbility
자가 평가 능력 (0-5 척도)

- language: 언어 능력
- math: 수리 능력
- science: 과학 능력
- coding: 코딩 능력
- design: 디자인 능력

### Evidence
능력 근거 자료

- grades: 성적
- activities: 활동
- awards: 수상

### AlternativeConfig
평가할 대안 (전공 리스트)

- majors: 전공 리스트 (최소 2개)

### SessionSettings
세션 설정

- max_criteria: 최대 기준 개수 (기본 5)
- cr_threshold: CR 임계값 (기본 0.10)
- cr_max_retries: CR 재시도 최대 횟수 (기본 3)
- enable_streaming: 스트리밍 출력 활성화 (기본 False)

## 2. Conversation State (models/state.py)

### ConversationState
LangGraph 워크플로우의 메인 상태입니다.

#### 사용자 입력
- user_input: 사용자 입력 전체

#### 에이전트 설정
- agent_weights: 에이전트 가중치 딕셔너리
- speaking_order: 발언 순서 리스트
- total_turns: 총 발언 횟수
- current_turn: 현재 발언 인덱스

#### 워크플로우 제어
- current_round: 현재 라운드 (1-4)
- workflow_status: 워크플로우 상태

#### Round 1: 기준 생성
- criteria_proposals: 모든 기준 제안 (List[CriteriaProposal])
- final_criteria: 최종 확정 기준

#### Round 2: AHP
- pairwise_comparisons: 모든 쌍대비교 (List[PairwiseComparison])
- integrated_ahp_matrix: 통합 쌍대비교 행렬
- criteria_weights: 기준 가중치
- eigenvalue_max: 최대 고유값
- consistency_index: CI 값
- consistency_ratio: CR 값
- cr_retry_count: CR 재시도 횟수
- cr_status: CR 상태

#### Round 3: 점수화
- agent_scores: 모든 점수 (List[AgentScore])
- integrated_decision_matrix: 통합 의사결정 행렬

#### Round 4: TOPSIS
- normalized_matrix: 정규화 행렬
- weighted_matrix: 가중 행렬
- ideal_solution: 이상해 (A+)
- anti_ideal_solution: 반이상해 (A-)
- topsis_results: TOPSIS 결과 (List[TOPSISResult])
- final_ranking: 최종 순위

#### 기타
- messages: 대화 히스토리
- errors: 에러 리스트
- warnings: 경고 리스트

### CriteriaProposal
에이전트의 기준 제안

```python
{
    "agent_name": str,           # 에이전트 이름
    "turn": int,                 # 발언 차례
    "criterion_name": str,       # 기준 이름
    "criterion_description": str,# 기준 설명
    "criterion_type": str,       # 'benefit' or 'cost'
    "reasoning": str             # 제안 이유
}
```

### PairwiseComparison
쌍대비교 데이터

```python
{
    "agent_name": str,           # 에이전트 이름
    "turn": int,                 # 발언 차례
    "criterion_a": str,          # 기준 A
    "criterion_b": str,          # 기준 B
    "comparison_value": float,   # 1-9 척도 비교값
    "reasoning": str             # 비교 근거
}
```

### AgentScore
에이전트의 대안 점수

```python
{
    "agent_name": str,           # 에이전트 이름
    "turn": int,                 # 발언 차례
    "major": str,                # 전공명
    "criterion": str,            # 기준명
    "score": float,              # 0-5 척도 점수
    "reasoning": str             # 점수 근거
}
```

### TOPSISResult
TOPSIS 계산 결과

```python
{
    "major": str,                        # 전공명
    "normalized_scores": Dict[str, float],  # 정규화 점수
    "weighted_scores": Dict[str, float],    # 가중 점수
    "distance_to_ideal": float,          # 이상해까지 거리
    "distance_to_anti_ideal": float,     # 반이상해까지 거리
    "closeness_coefficient": float,      # 근접도 계수
    "rank": int                          # 순위
}
```

## 3. Output Schema (models/output_schema.py)

### SessionOutput
최종 출력 스키마

```python
{
    "session_id": str,                   # 세션 ID
    "timestamp": str,                    # 타임스탬프
    "status": str,                       # 'success', 'partial', 'failed'
    "user_weights": Dict[str, int],      # 사용자 가중치
    "alternatives": List[str],           # 대안 리스트
    "criteria": List[CriterionDetail],   # 기준 상세
    "ahp_details": AHPDetail,            # AHP 상세
    "decision_matrix": Dict,             # 의사결정 행렬
    "final_ranking": List[MajorScore],   # 최종 순위
    "agent_contributions": List[AgentContribution],  # 에이전트 기여도
    "total_conversation_turns": int,     # 총 대화 횟수
    "execution_time_seconds": float,     # 실행 시간
    "errors": List[str],                 # 에러 리스트
    "warnings": List[str]                # 경고 리스트
}
```

### CriterionDetail
기준 상세 정보

- name: 기준 이름
- description: 기준 설명
- type: 'benefit' or 'cost'
- weight: AHP에서 계산된 가중치
- proposed_by: 제안한 에이전트 리스트

### AHPDetail
AHP 계산 상세

- criteria_weights: 기준별 가중치
- consistency_ratio: CR 값
- eigenvalue_max: 최대 고유값
- retry_count: 재시도 횟수
- status: 'passed' or 'failed'

### MajorScore
전공 점수 상세

- major: 전공명
- rank: 순위
- closeness_coefficient: TOPSIS 근접도
- criterion_scores: 기준별 원점수
- weighted_scores: 기준별 가중 점수
- distance_to_ideal: 이상해까지 거리
- distance_to_anti_ideal: 반이상해까지 거리

### AgentContribution
에이전트 기여도

- agent_name: 에이전트 이름
- weight: 할당된 가중치
- speaking_turns: 발언 횟수
- criteria_proposed: 제안한 기준 개수
- influence_score: 영향력 점수

## Data Flow

```
[UserInput]
    |
    v
[ConversationState] (초기화)
    |
    v
[Round 1: Criteria Generation]
    - CriteriaProposal 수집
    - final_criteria 확정
    |
    v
[Round 2: AHP]
    - PairwiseComparison 수집
    - integrated_ahp_matrix 생성
    - criteria_weights 계산
    - CR 검증 (재시도 루프)
    |
    v
[Round 3: Scoring]
    - AgentScore 수집
    - integrated_decision_matrix 생성
    |
    v
[Round 4: TOPSIS]
    - 정규화, 가중치 적용
    - ideal/anti_ideal 계산
    - TOPSISResult 생성
    - final_ranking 도출
    |
    v
[SessionOutput] (최종 출력)
```

## Validation Rules

### UserInput Validation
- agent_config 총합 = 10
- alternatives 최소 2개
- self_ability 각 항목 0-5 범위

### State Validation
- current_turn < total_turns
- current_round in [1, 2, 3, 4]
- cr_retry_count <= cr_max_retries

### Output Validation
- final_ranking 순서 보장 (rank 1, 2, 3, ...)
- closeness_coefficient 0-1 범위
- criteria_weights 합계 = 1.0
