import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";
import { executePythonScript } from "@/lib/python";
import {
  Round1Result,
  Round2Result,
  Round3Result,
  Round4Result,
  RoundAPIResponse,
} from "@/lib/types";

/**
 * POST /api/round/[id]
 * Execute Python debate scripts and return results
 * Body: { round: 1 | 2 | 3 | 4, sessionId: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { round: roundNumber, sessionId } = body;

    if (!sessionId || ![1, 2, 3, 4].includes(roundNumber)) {
      return NextResponse.json(
        { success: false, error: "Invalid round number or session ID" },
        { status: 400 }
      );
    }

    // Check if session exists
    const backendPath = path.join(process.cwd(), "..", "backend");
    const sessionFilePath = path.join(
      backendPath,
      "data",
      "user_inputs",
      `${sessionId}.json`
    );

    try {
      await readFile(sessionFilePath, "utf-8");
    } catch {
      return NextResponse.json(
        { success: false, error: "Session not found" },
        { status: 404 }
      );
    }

    // Execute Python script for the specific round
    const scriptName = `round${roundNumber}_debate.py`;

    console.log(`Executing ${scriptName} for session ${sessionId}...`);

    const result = await executePythonScript(scriptName, sessionId);

    if (!result.success) {
      return NextResponse.json(
        {
          success: false,
          error: result.error || `Failed to execute ${scriptName}`,
        },
        { status: 500 }
      );
    }

    // Read the output file
    const outputFilePath = path.join(
      backendPath,
      "output",
      `round${roundNumber}_${sessionId}.json`
    );

    let outputData: Round1Result | Round2Result | Round3Result | Round4Result;

    try {
      const outputContent = await readFile(outputFilePath, "utf-8");
      outputData = JSON.parse(outputContent);
    } catch (error) {
      console.error(`Failed to read output file:`, error);
      return NextResponse.json(
        {
          success: false,
          error: `Output file not found for round ${roundNumber}`,
        },
        { status: 500 }
      );
    }

    const response: RoundAPIResponse = {
      success: true,
      round: roundNumber,
      data: outputData,
      message: `Round ${roundNumber} completed successfully`,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Round API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
