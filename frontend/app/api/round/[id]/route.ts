import { NextRequest } from "next/server";
import { readFile } from "fs/promises";
import path from "path";
import { executePythonScript } from "@/lib/python";
import { spawn } from "child_process";

/**
 * POST /api/round/[id]
 * Execute Python debate scripts with streaming support for Round 1
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const body = await request.json();
    const { sessionId } = body;
    const { id } = await params;
    const roundNumber = parseInt(id);

    console.log('[API Round] Round:', roundNumber, 'Session:', sessionId);

    if (!sessionId || ![1, 2, 3, 4].includes(roundNumber)) {
      return new Response(
        JSON.stringify({ success: false, error: "Invalid round number or session ID" }),
        { status: 400 }
      );
    }

    const backendPath = path.join(process.cwd(), "..", "backend");
    const sessionFilePath = path.join(backendPath, "data", "user_inputs", `${sessionId}.json`);

    try {
      await readFile(sessionFilePath, "utf-8");
    } catch {
      return new Response(
        JSON.stringify({ success: false, error: "Session not found" }),
        { status: 404 }
      );
    }

    const scriptName = `round${roundNumber}_debate.py`;

    // Round 1은 스트리밍으로 전송
    if (roundNumber === 1) {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          try {
            const pythonProcess = spawn("python", ["scripts/" + scriptName, sessionId], {
              cwd: backendPath,
              env: { ...process.env, PYTHONPATH: backendPath },
            });

            let outputBuffer = "";
            let turnCount = 0;

            pythonProcess.stdout.on("data", (data) => {
              const text = data.toString();
              outputBuffer += text;

              // 각 턴 완료 시그널 감지 (토론 스크립트에서 출력)
              if (text.includes("TURN_COMPLETE:")) {
                turnCount++;
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({ type: "turn", turn: turnCount })}\n\n`)
                );
              }
            });

            pythonProcess.stderr.on("data", (data) => {
              console.error(`[Round 1 Error]: ${data.toString()}`);
            });

            pythonProcess.on("close", async (code) => {
              if (code === 0) {
                // 최종 결과 읽기
                const outputFilePath = path.join(backendPath, "output", `round1_${sessionId}.json`);
                try {
                  const outputContent = await readFile(outputFilePath, "utf-8");
                  const outputData = JSON.parse(outputContent);
                  controller.enqueue(
                    encoder.encode(`data: ${JSON.stringify({ type: "complete", data: outputData })}\n\n`)
                  );
                } catch (error) {
                  controller.enqueue(
                    encoder.encode(`data: ${JSON.stringify({ type: "error", error: "Failed to read output" })}\n\n`)
                  );
                }
              } else {
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({ type: "error", error: `Process exited with code ${code}` })}\n\n`)
                );
              }
              controller.close();
            });

          } catch (error) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ type: "error", error: String(error) })}\n\n`)
            );
            controller.close();
          }
        },
      });

      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    }

    // Round 2-4는 기존 방식 유지
    console.log(`Executing ${scriptName} for session ${sessionId}...`);

    const result = await executePythonScript(scriptName, sessionId);

    if (!result.success) {
      return new Response(
        JSON.stringify({ success: false, error: result.error || `Failed to execute ${scriptName}` }),
        { status: 500 }
      );
    }

    const outputFilePath = path.join(backendPath, "output", `round${roundNumber}_${sessionId}.json`);

    try {
      const outputContent = await readFile(outputFilePath, "utf-8");
      const outputData = JSON.parse(outputContent);
      return new Response(
        JSON.stringify({ success: true, round: roundNumber, data: outputData }),
        { headers: { "Content-Type": "application/json" } }
      );
    } catch (error) {
      console.error(`Failed to read output file:`, error);
      return new Response(
        JSON.stringify({ success: false, error: `Output file not found for round ${roundNumber}` }),
        { status: 500 }
      );
    }

  } catch (error) {
    console.error("Round API error:", error);
    return new Response(
      JSON.stringify({ success: false, error: "Internal server error" }),
      { status: 500 }
    );
  }
}
