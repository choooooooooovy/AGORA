# AGORA
**Agent Governance & Operational Ranking Automation**

An AI-powered multi-agent debate system for academic major selection and decision support

---

## Overview

AGORA is an AI decision-making system that recommends optimal academic majors based on user interests, aptitudes, and values.

### Core Features
- **Multi-Agent Debate System**: 3 AI agents engage in structured debates
- **AHP (Analytic Hierarchy Process)**: Calculate relative importance of evaluation criteria
- **TOPSIS**: Derive final rankings
- **Next.js Frontend**: Real-time visualization of debate processes

### Tech Stack
**Backend**
- Python 3.10+
- LangChain + OpenAI GPT-4o
- AHP / TOPSIS algorithms

**Frontend**
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui

---

## System Architecture

### Overall Workflow
```
User Input (interests, aptitudes, values, candidate majors)
    ↓
AI Agent Persona Generation (3 contrasting perspectives)
    ↓
Round 1: Criteria Selection (structured debate) → Select 4-5 criteria
    ↓
Round 2: AHP Weight Calculation (structured debate) → Calculate importance weights
    ↓
Round 3: Major Evaluation (structured debate) → Generate Decision Matrix
    ↓
Round 4: TOPSIS Ranking → Final major recommendations
```

### Debate Structure
Each round follows a structured debate format:
- **Phase 1-3**: Each agent leads in turn
  - Agent proposes solution
  - Other agents critique
  - Proposing agent defends
- **Phase 4**: Director makes final decision

---

## Project Structure

```
AGORA/
├── backend/
│   ├── core/
│   │   ├── persona_generator.py      # AI Agent Persona generation
│   │   └── workflow_engine.py        # Workflow orchestration
│   ├── workflows/
│   │   ├── round1_criteria.py        # Round 1: Criteria selection
│   │   ├── round2_ahp.py             # Round 2: AHP weighting
│   │   ├── round3_scoring.py         # Round 3: Major evaluation
│   │   └── round4_topsis.py          # Round 4: TOPSIS ranking
│   ├── utils/
│   │   ├── ahp_calculator.py         # AHP calculation logic
│   │   └── topsis_calculator.py      # TOPSIS calculation logic
│   ├── scripts/
│   │   ├── generate_personas.py      # Persona generation script
│   │   └── round*_debate.py          # Round execution scripts
│   └── output/                       # Round results (JSON)
│
└── frontend/
    ├── app/
    │   ├── page.tsx                  # Main page
    │   └── api/                      # API Routes
    │       ├── user-input/           # Persona generation
    │       ├── round/[id]/           # Round execution
    │       └── report/[sessionId]/   # Final report
    ├── components/
    │   ├── UserInputForm.tsx         # User input form
    │   ├── AgentConversation.tsx     # Debate visualization (core)
    │   ├── CriteriaWeightsPanel.tsx  # AHP weights visualization
    │   ├── DecisionMatrixTable.tsx   # Decision Matrix table
    │   └── ReviewExport.tsx          # Final recommendations
    └── lib/
        ├── types.ts                  # TypeScript type definitions
        └── python.ts                 # Python backend integration
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Installation

**Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

**Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### Running the Application
1. Start frontend: `http://localhost:3000`
2. Enter user input → Generate AI agents → Run Rounds 1-4 → View final recommendations

---

## Key Features

### 1. Automatic AI Agent Generation
Analyzes user input text to extract 3 contrasting perspectives:
- Example: "Economic success priority", "Social impact priority", "Work-life balance priority"

### 2. Real-time Debate Visualization
- Messages appear sequentially with animations
- Dynamic delay based on message length
- Automatic JSON parsing and formatting

### 3. Structured Decision Process
- Round 1: Consensus on evaluation criteria
- Round 2: Calculate criteria importance (AHP)
- Round 3: Score majors on each criterion
- Round 4: Derive final rankings (TOPSIS)

### 4. Transparent Results
- Full debate transcripts for each round
- Visualization of AHP weights, Decision Matrix, TOPSIS calculations
- Strength/weakness analysis for each major

---

## User Input Format

### Example Input
```json
{
  "interests": "I enjoy solving complex mathematical problems and implementing algorithms. I like keeping up with tech trends...",
  "aptitudes": "Strong logical thinking and coding skills. Creative problem-solving approach...",
  "core_values": "I want high salary and rapid career growth, but work-life balance is also important...",
  "candidate_majors": ["Computer Science", "Electrical Engineering", "Industrial Engineering", "Business Administration"],
  "settings": {
    "max_criteria": 5,
    "cr_threshold": 0.10
  }
}
```

### Field Descriptions
- **interests**: User's interests, hobbies, favorite activities
- **aptitudes**: Strengths, talents, capabilities
- **core_values**: Values, priorities, what matters most
- **candidate_majors**: List of majors to evaluate (minimum 2)
- **settings.max_criteria**: Number of evaluation criteria (default: 5)
- **settings.cr_threshold**: AHP consistency ratio threshold (default: 0.10)

---

## Methodology

### AHP (Analytic Hierarchy Process)
- Pairwise comparison between criteria to calculate relative importance
- Uses Saaty Scale (1-9, 0.5 increments)
- Consistency Ratio (CR) validation (must be ≤ 0.10)

### TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
- Normalize Decision Matrix and apply weights
- Calculate distances from ideal (A+) and anti-ideal (A-) solutions
- Derive final rankings based on closeness coefficient

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/user-input` | POST | User input → AI Persona generation |
| `/api/round/1` | POST | Round 1: Criteria selection |
| `/api/round/2` | POST | Round 2: AHP weight calculation |
| `/api/round/3` | POST | Round 3: Major evaluation |
| `/api/round/4` | POST | Round 4: TOPSIS ranking |
| `/api/report/[sessionId]` | GET | Retrieve complete session data |

---

## Known Limitations

- **Language Support**: Currently Korean only
- **OpenAI Dependency**: Requires GPT-4o model
- **Session Management**: JSON file-based (no database)
- **Concurrent Users**: Potential session_id conflicts

---

## Contributing

### Code Style
- Python: PEP 8, type hints recommended
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits format

### Pull Request Process
1. Create feature branch
2. Commit changes
3. Create Pull Request

---

## Authors

**choooooooooovy** - [GitHub](https://github.com/choooooooooovy) | [LinkedIn](https://www.linkedin.com/in/%EC%A7%84%EC%98%81-%EC%B5%9C-18a6282b1/)

---