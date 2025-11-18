/**
 * 백엔드 출력 구조와 정확히 일치하는 TypeScript 타입 정의
 */

// ============================================================================
// Agent Persona Types
// ============================================================================

export interface AgentPersona {
  name: string;
  perspective: string;
  persona_description: string;
  key_strengths: string[];
  debate_stance: string;
  system_prompt: string;
}

// Frontend용 확장 (avatar, color는 프론트엔드에서 생성)
export interface AgentPersonaWithUI extends AgentPersona {
  avatar: string;
  color: string;
}

// ============================================================================
// User Input Types
// ============================================================================

export interface UserInput {
  interests: string;
  aptitudes: string;
  core_values: string;
  candidate_majors: string[];
  settings: {
    max_criteria: number;
    cr_threshold: number;
    cr_max_retries: number;
    enable_streaming: boolean;
  };
}

// ============================================================================
// Debate Turn Types
// ============================================================================

export interface DebateTurn {
  turn: number;
  phase: string;
  speaker: string;
  type: "proposal" | "question" | "answer" | "debate" | "decision";
  target: string | string[] | null;
  content: string;
  timestamp: string;
}

// ============================================================================
// Round 1: Criteria Selection
// ============================================================================

export interface SelectedCriterion {
  criterion: string;
  description: string;
}

export interface Round1DirectorDecision {
  selected_criteria: SelectedCriterion[];
  rationale: string;
  timestamp: string;
}

export interface Round1Result {
  round1_debate_turns: DebateTurn[];
  selected_criteria: SelectedCriterion[];
  round1_director_decision: Round1DirectorDecision;
}

// ============================================================================
// Round 2: AHP Weight Calculation
// ============================================================================

export interface Round2Result {
  round2_debate_turns: DebateTurn[];
  comparison_matrix: Record<string, number>;
  criteria_weights: Record<string, number>;
  consistency_ratio: number;
  round2_director_decision?: {
    final_weights: Record<string, number>;
    rationale: string;
    timestamp: string;
  };
}

// ============================================================================
// Round 3: Scoring Alternatives
// ============================================================================

export interface DecisionMatrix {
  [major: string]: {
    [criterion: string]: number;
  };
}

export interface Round3Result {
  round3_debate_turns: DebateTurn[];
  decision_matrix: DecisionMatrix;
}

// ============================================================================
// Round 4: TOPSIS Final Ranking
// ============================================================================

export interface TOPSISRanking {
  major: string;
  rank: number;
  closeness_coefficient: number;
}

export interface TOPSISResult {
  final_ranking: TOPSISRanking[];
  positive_ideal: Record<string, number>;
  negative_ideal: Record<string, number>;
  details: {
    normalized_matrix: DecisionMatrix;
    weighted_matrix: DecisionMatrix;
    separations: {
      [major: string]: {
        positive: number;
        negative: number;
      };
    };
  };
}

export interface Round4Result {
  topsis_result: TOPSISResult;
  final_ranking: TOPSISRanking[];
}

// ============================================================================
// Complete Conversation State
// ============================================================================

export interface ConversationState {
  session_id: string;
  user_input: UserInput;
  agent_personas: AgentPersona[];

  // Round 1
  round1_debate_turns?: DebateTurn[];
  selected_criteria?: SelectedCriterion[];
  round1_director_decision?: Round1DirectorDecision;

  // Round 2
  round2_debate_turns?: DebateTurn[];
  comparison_matrix?: Record<string, number>;
  criteria_weights?: Record<string, number>;
  consistency_ratio?: number;

  // Round 3
  round3_debate_turns?: DebateTurn[];
  decision_matrix?: DecisionMatrix;

  // Round 4
  topsis_result?: TOPSISResult;
  final_ranking?: TOPSISRanking[];
}

// ============================================================================
// API Response Types
// ============================================================================

export interface UserInputAPIResponse {
  success: boolean;
  session_id: string;
  agent_personas: AgentPersona[];
  message?: string;
  error?: string;
}

export interface RoundAPIResponse {
  success: boolean;
  round: number;
  data: Round1Result | Round2Result | Round3Result | Round4Result;
  message?: string;
  error?: string;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface UIAgent extends AgentPersonaWithUI {
  id: number;
  // UI용 추가 필드 (백엔드 persona_description을 UI에 맞게 변환)
  role: string; // perspective를 role로 표시
  personality: string; // persona_description을 personality로 표시
  strengths: string[]; // key_strengths를 strengths로 표시
}

export interface Message {
  id: number;
  agentId: number;
  agentName: string;
  agentAvatar: string;
  agentColor: string;
  content: string;
  timestamp: string;
  type?: "proposal" | "question" | "answer" | "debate" | "decision";
}
