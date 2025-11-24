/**
 * API Client for AGORA Backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UserInputData {
  interests: string;
  aptitudes: string;
  core_values: string;
  candidate_majors: string[];
}

interface Persona {
  name: string;
  perspective: string;
  persona_description: string;
  key_strengths: string[];
  debate_stance: string;
  system_prompt: string;
}

interface UserInputResponse {
  success: boolean;
  session_id: string;
  message: string;
  personas?: Persona[];
}

interface RoundResponse {
  success: boolean;
  session_id: string;
  round: number;
  message: string;
  data?: Record<string, unknown>;
}

interface ReportResponse {
  success: boolean;
  session_id: string;
  report?: Record<string, unknown>;
}

/**
 * Submit user input and generate personas
 */
export async function submitUserInput(data: UserInputData): Promise<UserInputResponse> {
  const response = await fetch(`${API_URL}/api/user-input`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to submit user input');
  }

  return response.json();
}

/**
 * Execute a specific round
 */
export async function executeRound(roundNumber: number, sessionId: string): Promise<RoundResponse> {
  const response = await fetch(`${API_URL}/api/round/${roundNumber}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to execute round ${roundNumber}`);
  }

  return response.json();
}

/**
 * Get final report
 */
export async function getReport(sessionId: string): Promise<ReportResponse> {
  const response = await fetch(`${API_URL}/api/report/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get report');
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; openai_configured: boolean }> {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error('Backend is not available');
  }

  return response.json();
}

/**
 * Generate session ID (for compatibility)
 */
export function generateSessionId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 12);
  return `${timestamp}-${random}`;
}
