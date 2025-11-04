# Data Schema Documentation

## Overview

This document describes the data schema structure of the Prioritization Framework.

---

## 1. User Input Schema (data/user_inputs/sample_template_new.json)

### UserInput
Main schema containing all user input data.

```json
{
  "mbti": "<One of 16 MBTI types>",
  "strengths": ["<strength1>", "<strength2>", "..."],
  "weaknesses": ["<weakness1>", "<weakness2>", "..."],
  "favorite_subjects": ["<favorite1>", "<favorite2>", "..."],
  "disliked_subjects": ["<disliked1>", "<disliked2>", "..."],
  "good_at_subjects": ["<good_at1>", "<good_at2>", "..."],
  "bad_at_subjects": ["<bad_at1>", "<bad_at2>", "..."],
  "core_values": ["<value1>", "<value2>", "..."],
  "candidate_majors": ["<major1>", "<major2>", "..."],
  "settings": {
    "max_criteria": 5,
    "cr_threshold": 0.10,
    "cr_max_retries": 3,
    "enable_streaming": false
  }
}
```

### Field Descriptions

#### User Characteristics
- **mbti**: MBTI personality type
- **strengths**: List of user's strengths (free format)
- **weaknesses**: List of user's weaknesses (free format)
- **favorite_subjects**: List of favorite subjects (free format)
- **disliked_subjects**: List of disliked subjects (free format)
- **good_at_subjects**: List of subjects user excels at (free format)
- **bad_at_subjects**: List of subjects user struggles with (free format)
- **core_values**: List of user's core values (free format, distributed to Agents during generation)

#### Evaluation Targets
- **candidate_majors**: List of majors to evaluate (minimum 2, free format)

#### Session Settings
- **settings.max_criteria**: Maximum number of criteria (default 5)
- **settings.cr_threshold**: AHP Consistency Ratio threshold (default 0.10)
- **settings.cr_max_retries**: Maximum CR retry attempts (default 3)
- **settings.enable_streaming**: Enable streaming output (default false)

---

## 2. Agent Personas (Auto-generated)

Generated automatically by the workflow engine based on user's `core_values`.

### AgentPersona Structure

```python
{
  "name": "<Unique agent name>",  # Auto-generated agent name
  "core_values": ["<value1>", "<value2>"],  # Assigned values (1-2 per agent)
  "persona_description": "<Persona description>",  # Personality and perspective
  "debate_stance": "<Debate stance>",  # Argumentation direction in debates
  "system_prompt": "<LLM prompt>"  # Agent's system prompt
}
```

### Generation Rules
- User's `core_values` are **evenly distributed** among **3 Agents**
- Each Agent is assigned **1-2 values**
- Personas are auto-generated reflecting user characteristics (MBTI, strengths, weaknesses)
- Agent names are auto-generated to reflect their assigned values

---

## 3. Conversation State (models/state.py)

### ConversationState
Main state for the LangGraph workflow.

#### Basic Information
- **user_input**: Complete user input (dict)
- **session_id**: Unique session ID
- **alternatives**: List of majors to evaluate (from user_input's candidate_majors)
- **agent_personas**: List of generated agent personas

#### Round 1: Criteria Selection (13-turn Debate)
- **round1_debate_turns**: 13-turn debate history (List[dict])
  - turn, phase, speaker, type, content, timestamp
- **selected_criteria**: Final selected criteria list (List[dict])
  - name, description, type, source_agent, reasoning

#### Round 2: AHP Pairwise Comparison (13-turn Debate)
- **round2_debate_turns**: 13-turn debate history (List[dict])
  - turn, phase, speaker, type, content, comparison_matrix, timestamp
- **comparison_matrix**: Final comparison matrix (Dict[str, float])
  - key: "CriteriaA vs CriteriaB", value: Saaty scale (1.0-9.0, 0.5 increments)
- **criteria_weights**: AHP weights (Dict[str, float])
- **consistency_ratio**: CR value (float)
- **eigenvalue_max**: Maximum eigenvalue (float)
- **round2_director_decision**: Director's final decision

#### Round 3: Decision Matrix (13-turn Debate)
- **round3_debate_turns**: 13-turn debate history (List[dict])
  - turn, phase, speaker, type, content, decision_matrix, timestamp
- **decision_matrix**: Final Decision Matrix (Dict[str, Dict[str, float]])
  - key1: major name, key2: criteria name, value: score (1.0-9.0, 0.5 increments)
- **round3_director_decision**: Director's final decision
  - decision_matrix, reasoning

#### Round 4: TOPSIS Ranking Calculation
- **normalized_matrix**: Normalized matrix
- **weighted_matrix**: Weighted matrix
- **ideal_solution**: Ideal solution (A+)
- **anti_ideal_solution**: Anti-ideal solution (A-)
- **topsis_results**: TOPSIS results
- **final_ranking**: Final ranking

---

## 4. Debate Turn Structure

### 13-Turn Debate System
All Rounds (1, 2, 3) use the same 13-turn structure.

#### Phase 1-3: Agent-led Phases (4 turns × 3 = 12 turns)
```python
{
  "turn": 1,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "PassionDriven",
  "type": "proposal",  # Proposal
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 2,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "PragmaticEarner",
  "type": "critique",  # Critique
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 3,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "SocialContributor",
  "type": "critique",  # Critique
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 4,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "PassionDriven",
  "type": "defense",  # Rebuttal
  "target": ["PragmaticEarner", "SocialContributor"],
  "content": "...",
  "timestamp": "..."
}
```

#### Phase 4: Director's Final Decision (1 turn)
```python
{
  "turn": 13,
  "phase": "Phase 4: Director's final decision",
  "speaker": "Director",
  "type": "final_decision",
  "content": "...",
  "timestamp": "..."
}
```

### Round-specific Additional Fields

**Round 1**: selected_criteria (final selected criteria)
**Round 2**: comparison_matrix (comparison matrix)
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
[Auto-generate Agent Personas]
    ↓
┌─────────────────────────────────────────┐
│ Round 1: Criteria Selection (13 turns)  │
│ - Each Agent proposes criteria          │
│ - Director selects final 5 criteria     │
│ → selected_criteria                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 2: AHP Comparison (13 turns)      │
│ - 10 pairwise comparisons (nC2, n=5)    │
│ - Director finalizes comparison matrix  │
│ - Calculate AHP weights                 │
│ → criteria_weights, CR                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 3: Decision Matrix (13 turns)     │
│ - Score all major × criteria combos     │
│ - Director finalizes matrix             │
│ → decision_matrix                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Round 4: TOPSIS Ranking                 │
│ - Normalize and apply weights           │
│ - Calculate ideal/anti-ideal solutions  │
│ - Derive final ranking                  │
│ → final_ranking                         │
└─────────────────────────────────────────┘
```

---

## 7. Validation Rules

### User Input Validation
- `mbti`: One of 16 MBTI types
- `candidate_majors`: Minimum 2 items
- `core_values`: Minimum 1 item (required for Agent generation)
- `settings.max_criteria`: Range 3-10
- `settings.cr_threshold`: Range 0.05-0.20

### Round 1 Validation
- `selected_criteria`: Exactly max_criteria items

### Round 2 Validation
- `comparison_matrix`: nC2 pairwise comparisons (n = len(selected_criteria))
- All comparison values: 0.5 increments (1.0, 1.5, 2.0, ..., 9.0)
- `consistency_ratio`: ≤ cr_threshold

### Round 3 Validation
- `decision_matrix`: All (major × criteria) combinations present
- All scores: 0.5 increments (1.0, 1.5, 2.0, ..., 9.0)
- Score diversity: Same score ≤3 times recommended

### Round 4 Validation
- `final_ranking`: No duplicate ranks (1, 2, 3, ...)
- `closeness_coefficient`: Range 0.0-1.0
- Weight sum: 1.0

---

## 8. Score Guides

### Round 2: AHP Saaty Scale (1-9, 0.5 increments)

**[1.0 - 2.5] Equal to Slightly Important**
- 1.0: Equal - Two criteria are at the same level
- 1.5: Nearly equal - Very minor difference
- 2.0: Slightly important - A bit more important
- 2.5: Moderately slightly important - Starting to be noticeable

**[3.0 - 5.0] Important to Very Important**
- 3.0: Important - Clearly more important
- 3.5: Considerably important - Definite difference
- 4.0: Very important - Significantly more important
- 4.5: Highly important - Large difference
- 5.0: Essential - Critical difference

**[5.5 - 9.0] Extremely Important to Absolute**
- 5.5-7.0: Extremely important
- 7.5-9.0: Absolutely important (rarely used)

### Round 3: Decision Matrix Scale (1-9, 0.5 increments)

**[1.0 - 3.0] Poor Fit**
- 1.0-2.0: Very poor fit ~ Poor fit
- 2.5-3.0: Somewhat poor ~ Rather poor

**[3.5 - 5.5] Moderate Fit**
- 3.5-4.0: Below moderate ~ Moderate
- 4.5-5.0: Above moderate ~ Good fit
- 5.5: Quite good fit

**[6.0 - 9.0] Good Fit**
- 6.0-7.0: Very good fit ~ Excellent fit
- 7.5-8.5: Highly excellent ~ Nearly perfect
- 9.0: Perfect fit (rarely used)

**Score Distribution Guidelines:**
- Most scores: 3-7 range
- 8-9 scores: Exceptional cases only (≤5%)
- 1-2 scores: Clearly poor fit only (≤5%)
```