import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

    // Call backend API
    const response = await fetch(`${API_URL}/api/user-input`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || 'Failed to process user input' },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Transform response to match frontend expectations
    return NextResponse.json({
      success: data.success,
      message: data.message,
      session_id: data.session_id,
      agent_personas: data.personas || [],
    });

  } catch (error) {
    console.error("Error in user-input API:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 }
    );
  }
}

