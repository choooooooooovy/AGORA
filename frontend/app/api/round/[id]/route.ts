import { NextRequest } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * POST /api/round/[id]
 * Execute debate rounds by calling backend API
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
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Call backend API
    const response = await fetch(`${API_URL}/api/round/${roundNumber}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      const error = await response.json();
      return new Response(
        JSON.stringify({
          success: false,
          error: error.detail || `Failed to execute round ${roundNumber}`
        }),
        { status: response.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await response.json();

    return new Response(
      JSON.stringify({
        success: data.success,
        round: data.round,
        data: data.data
      }),
      { headers: { "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("Round API error:", error);
    return new Response(
      JSON.stringify({ success: false, error: "Failed to connect to backend" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
