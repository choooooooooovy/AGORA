import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import path from "path";
import { generateSessionId, executePythonScript } from "@/lib/python";

interface UserInputRequest {
  interests: string;
  aptitudes: string;
  core_values: string;
  candidate_majors: string[];
}

export async function POST(request: NextRequest) {
  try {
    const body: UserInputRequest = await request.json();

    // Validate input
    if (
      !body.interests ||
      !body.aptitudes ||
      !body.core_values ||
      !body.candidate_majors ||
      body.candidate_majors.length < 2
    ) {
      return NextResponse.json(
        { error: "Invalid input data" },
        { status: 400 }
      );
    }

    // Generate session ID
    const sessionId = generateSessionId();

    // Prepare user input data
    const userInputData = {
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      interests: body.interests,
      aptitudes: body.aptitudes,
      core_values: body.core_values,
      candidate_majors: body.candidate_majors,
      settings: {
        max_criteria: 4,
        cr_threshold: 0.1,
        cr_max_retries: 3,
        enable_streaming: false,
      },
    };

    // Save to backend/data/user_inputs/{session_id}.json
    const backendPath = path.join(process.cwd(), "..", "backend");
    const userInputsDir = path.join(backendPath, "data", "user_inputs");
    const filePath = path.join(userInputsDir, `${sessionId}.json`);

    // Ensure directory exists
    await mkdir(userInputsDir, { recursive: true });

    // Write file
    await writeFile(filePath, JSON.stringify(userInputData, null, 2));

    console.log(`[API] User input saved: ${filePath}`);

    // Execute persona generation only (fast, ~5 seconds)
    const personaResult = await executePythonScript("generate_personas.py", sessionId);

    if (!personaResult.success) {
      console.error("[API] Persona generation failed:", personaResult.error);
      return NextResponse.json(
        { error: "Failed to generate agent personas" },
        { status: 500 }
      );
    }

    // Read persona output
    const { readFile: readFilePromise } = await import("fs/promises");
    const personaOutputPath = path.join(backendPath, "output", `personas_${sessionId}.json`);

    try {
      const personaData = JSON.parse(await readFilePromise(personaOutputPath, "utf-8"));

      return NextResponse.json({
        success: true,
        message: "User input received and personas generated",
        session_id: sessionId,
        agent_personas: personaData.agent_personas || [],
      });
    } catch (error) {
      console.error("[API] Failed to read persona output:", error);
      return NextResponse.json(
        { error: "Persona generation completed but failed to read results" },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error("Error in user-input API:", error);
    return NextResponse.json(
      { error: "Failed to process user input" },
      { status: 500 }
    );
  }
}

