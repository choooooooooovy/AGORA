# AGORA - Agent Governance & Operational Ranking Automation

## Overview

AGORA is an AI-powered decision-making framework that helps users select academic majors (or alternatives) based on their interests, aptitudes, and core values.

**Core Methodologies**:
- **Multi-Agent Debate System** (3 AI agents engage in 13-turn structured debates)
- **AHP (Analytic Hierarchy Process)** - Calculate criteria weights
- **TOPSIS** - Determine final rankings

---

## 1. User Input Schema

### UserInput Structure

Simplified user input based on 3 free-text fields:

```json
{
  "interests": "<Free text: interests, passions, favorite activities>",
  "aptitudes": "<Free text: strengths, talents, capabilities>",
  "core_values": "<Free text: values, priorities, what matters most>",
  "candidate_majors": ["<major1>", "<major2>", "..."],
  "settings": {
    "max_criteria": 5,
    "cr_threshold": 0.10,
    "cr_max_retries": 3,
    "enable_streaming": false
  }
}
```

### Example

```json
{
  "interests": "I enjoy solving complex mathematical problems and implementing algorithms through programming. I like keeping up with the latest tech trends and learning new tools. I find it fascinating to analyze data and extract insights, and I'm interested in understanding and optimizing complex systems.",
  
  "aptitudes": "I have strong logical thinking and coding skills. I approach problem-solving creatively and have won awards in math competitions. I can systematically plan and execute tasks, quickly grasp complex concepts and apply them. I've demonstrated leadership in team projects.",
  
  "core_values": "I want high salary and rapid career growth, ideally working for a global company. However, work-life balance is also important to me, and I seek a sustainable long-term career. I want to do meaningful work that has a positive impact on many people through my creations. I value environments where I can continuously develop my expertise.",
  
  "candidate_majors": ["Computer Science", "Electrical Engineering", "Industrial Engineering", "Business Administration"],
  
  "settings": {
    "max_criteria": 5,
    "cr_threshold": 0.10,
    "cr_max_retries": 3,
    "enable_streaming": false
  }
}
```

### Field Descriptions

#### User Characteristics (Free Text)
- **interests**: User's interests, passions, and favorite activities (minimum 10 characters)
- **aptitudes**: User's strengths, talents, and capabilities (minimum 10 characters)
- **core_values**: User's values, priorities, and what matters most to them (minimum 10 characters)

#### Evaluation Targets
- **candidate_majors**: List of majors to evaluate (minimum 2)

#### Session Settings
- **settings.max_criteria**: Maximum number of evaluation criteria (default: 5)
- **settings.cr_threshold**: AHP Consistency Ratio threshold (default: 0.10)
- **settings.cr_max_retries**: Maximum CR retry attempts (default: 3)
- **settings.enable_streaming**: Enable streaming output (default: false)

---

## 2. Agent Personas

The LLM analyzes the user's interests/aptitudes/values text to extract **3 contrasting perspectives** 
and automatically generates agents representing each perspective.

### AgentPersona Structure

```python
{
  "name": "<Agent name>",  # English CamelCase (e.g., CareerMaximizer, ImpactSeeker)
  "perspective": "<Core perspective>",  # The perspective this agent represents (10-30 chars)
  "persona_description": "<Persona description>",  # Agent's identity and philosophy (200-400 chars)
  "debate_stance": "<Debate stance>",  # Core argument in debates (50-100 chars)
  "system_prompt": "<LLM prompt>"  # Agent's system prompt
}
```

### Generation Example

**Input Values**:
```
"I want high salary and rapid career growth, ideally working for a global company. 
However, work-life balance is also important to me, and I want to do socially meaningful work."
```

**3 Generated Contrasting Perspectives**:
1. **CareerMaximizer** - "Economic Success & Rapid Growth"
   - Prioritizes high salary, global companies, fast advancement
   
2. **ImpactSeeker** - "Social Impact & Meaning"
   - Prioritizes social contribution, meaningful outcomes
   
3. **BalancedGrowth** - "Sustainable Happiness"
   - Prioritizes work-life balance, long-term perspective, personal well-being

### Generation Rules
- LLM deeply analyzes user's interests/aptitudes/values text
- Automatically discovers **inherent tensions** (e.g., economic vs meaning vs balance)
- Designs 3 perspectives to create **constructive conflicts**
- Each agent consistently advocates their perspective

---

## 3. Workflow Architecture

### Round 1: Criteria Selection (13-turn Debate)
**Objective**: Reach consensus on **up to 5 evaluation criteria**

**Debate Structure** (Phase 1-3: Each agent leads):
```
Phase 1 (Agent A leads):
  Turn 1: Agent A proposes criteria
  Turn 2: Agent B questions A
  Turn 3: Agent C questions A
  Turn 4: Agent A answers B & C

Phase 2 (Agent B leads): Same structure
Phase 3 (Agent C leads): Same structure

Phase 4:
  Turn 13: Director makes final decision on 5 criteria
```

### Round 2: AHP Weight Calculation (13-turn Debate)
**Objective**: Determine **relative importance** of the 5 selected criteria

**Methodology**:
- **Pairwise Comparison**: 5 criteria → 10 comparison pairs
- AHP scale: 1-9 (0.5 increments), including reciprocals
- **CR (Consistency Ratio) validation**: Must be ≤ 0.10 for consistency

### Round 3: Decision Matrix Generation (13-turn Debate)
**Objective**: Score each major on each criterion

**Evaluation Scale**: 1-9 (0.5 increments)
- 1-3: Unsuitable
- 4-5: Average
- 6-9: Suitable/Excellent

### Round 4: TOPSIS Final Ranking
**Objective**: Calculate **final ranking** using Decision Matrix + weights

**TOPSIS Algorithm**:
1. Normalize Decision Matrix
2. Apply weights (Weighted Normalized Matrix)
3. Calculate Ideal and Anti-Ideal solutions
4. Calculate relative closeness coefficient for each alternative
5. Rank alternatives

---

## 4. State Schema (models/state.py)

### ConversationState
Main state for the workflow.

#### Basic Information
- **user_input**: Complete user input (dict)
- **session_id**: Unique session ID
- **agent_personas**: List of generated agent personas

#### Round 1: Criteria Selection (13-turn Debate)
- **round1_debate_turns**: 13-turn debate history (List[dict])
- **selected_criteria**: Final selected criteria list (List[dict])

#### Round 2: AHP Pairwise Comparison (13-turn Debate)
- **round2_debate_turns**: 13-turn debate history (List[dict])
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
  "type": "proposal",  
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 2,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "PragmaticEarner",
  "type": "critique",  
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 3,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "SocialContributor",
  "type": "critique",  
  "target": "PassionDriven",
  "content": "...",
  "timestamp": "..."
}

{
  "turn": 4,
  "phase": "Phase 1: PassionDriven leads",
  "speaker": "PassionDriven",
  "type": "defense",  
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
- `interests`: Free-text (minimum 10 characters)
- `aptitudes`: Free-text (minimum 10 characters)
- `core_values`: Free-text describing user's priorities (minimum 10 characters)
- `candidate_majors`: Minimum 2 items
- `settings.max_criteria`: Range 3-10
- `settings.cr_threshold`: Range 0.05-0.20

### Round 1 Validation
- `selected_criteria`: Exactly `settings.max_criteria` items (typically 3-5)

### Round 2 Validation
- `comparison_matrix`: nC2 pairwise comparisons (n = len(selected_criteria))
- All comparison values: 0.5 increments (1.0, 1.5, 2.0, ..., 9.0)
- `consistency_ratio`: ≤ `settings.cr_threshold`

### Round 3 Validation
- `decision_matrix`: All (major × criteria) combinations present
- All scores: 0.5 increments (1.0, 1.5, 2.0, ..., 9.0)
- Score diversity: Avoid using identical scores for many cells (same score ≤3 times recommended)

### Round 4 Validation
- `final_ranking`: No duplicate ranks (1, 2, 3, ...)
- `closeness_coefficient`: Range 0.0-1.0
- Weight sum: 1.0

---