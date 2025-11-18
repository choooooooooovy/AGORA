import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

/**
 * Python 스크립트를 실행합니다 (백엔드 round scripts용)
 */
export async function executePythonScript(
  scriptName: string,
  sessionId: string
): Promise<{ success: boolean; stdout?: string; stderr?: string; error?: string }> {
  const backendPath = path.join(process.cwd(), "..", "backend");

  // Round script는 session_id를 인자로 받음
  const command = `cd ${backendPath} && python scripts/${scriptName} ${sessionId}`;

  console.log(`[Python] Executing: ${command}`);

  try {
    const result = await execAsync(command);
    return {
      success: true,
      stdout: result.stdout,
      stderr: result.stderr
    };
  } catch (error) {
    console.error(`[Python] Error executing ${scriptName}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      stderr: (error as { stderr?: string }).stderr
    };
  }
}

/**
 * UUID 생성
 */
export function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
