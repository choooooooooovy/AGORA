"use client";

import { useState, useEffect } from "react";
import { UserInputForm } from "@/components/UserInputForm";
import { AgentCard } from "@/components/AgentCard";
import { StepNavigator } from "@/components/StepNavigator";
import { UIAgent, Round1Result, Round2Result, Round3Result, TOPSISResult } from "@/lib/types";
import { AgentConversation } from "@/components/AgentConversation";
import { ReviewExport } from "@/components/ReviewExport";

export default function App() {
  // User Input State
  const [interests, setInterests] = useState("");
  const [aptitudes, setAptitudes] = useState("");
  const [pursuitValues, setPursuitValues] = useState("");
  const [candidateMajors, setCandidateMajors] = useState<string[]>([]);

  // Session & Agent State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agents, setAgents] = useState<UIAgent[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Round Data State
  const [round1Data, setRound1Data] = useState<Round1Result | null>(null);
  const [round2Data, setRound2Data] = useState<Round2Result | null>(null);
  const [round3Data, setRound3Data] = useState<Round3Result | null>(null);
  const [round4Data, setRound4Data] = useState<TOPSISResult | null>(null);
  const [isLoadingRound, setIsLoadingRound] = useState(false);

  // Navigation State
  const [currentStep, setCurrentStep] = useState(1);
  const [currentSubStep, setCurrentSubStep] = useState(1);

  // Error State
  const [error, setError] = useState<string | null>(null);

  const steps = [
    { id: 1, label: "에이전트 생성" },
    { id: 2, label: "에이전트 대화" },
    { id: 3, label: "분석 리포트" },
  ];

  const conversationSubSteps = [
    { id: 1, label: "평가 기준 선택" },
    { id: 2, label: "기준 가중치 산출" },
    { id: 3, label: "대안(학과)간 평가" },
  ];

  // Mock major recommendations
  const mockRecommendations = [
    { major: "컴퓨터공학", rank: 1, closeness_coefficient: 0.7954 },
    { major: "데이터사이언스", rank: 2, closeness_coefficient: 0.7821 },
    { major: "철학", rank: 3, closeness_coefficient: 0.7645 },
    { major: "인지과학", rank: 4, closeness_coefficient: 0.7432 },
    { major: "정보시스템", rank: 5, closeness_coefficient: 0.7201 },
    { major: "응용수학", rank: 6, closeness_coefficient: 0.6987 },
    { major: "인공지능", rank: 7, closeness_coefficient: 0.6854 },
    { major: "윤리와 기술", rank: 8, closeness_coefficient: 0.6723 },
    { major: "디지털인문학", rank: 9, closeness_coefficient: 0.6598 },
    { major: "비즈니스 애널리틱스", rank: 10, closeness_coefficient: 0.6412 },
  ];

  // Step 2 진입 시 Round 1 자동 실행
  useEffect(() => {
    if (currentStep === 2 && currentSubStep === 1 && !round1Data && sessionId && !isLoadingRound) {
      runRound1();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentStep, currentSubStep, sessionId]);

  // Generate agents by calling /api/user-input
  const generateAgents = async () => {
    setIsGenerating(true);
    setAgents([]);
    setError(null);

    try {
      const response = await fetch("/api/user-input", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          interests,
          aptitudes,
          core_values: pursuitValues,
          candidate_majors: candidateMajors,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();

      // Save session ID
      setSessionId(data.session_id);

      // Convert backend personas to UI agents
      const uiAgents: UIAgent[] = data.agent_personas.map((persona: { name: string; perspective: string; persona_description: string; key_strengths: string[]; debate_stance: string; system_prompt: string }, index: number) => {
        const colors = [
          "bg-gradient-to-br from-cyan-500 to-blue-600",
          "bg-gradient-to-br from-emerald-500 to-teal-600",
          "bg-gradient-to-br from-amber-500 to-orange-600",
        ];

        return {
          id: index + 1,
          name: persona.name,
          perspective: persona.perspective,
          persona_description: persona.persona_description,
          key_strengths: persona.key_strengths,
          debate_stance: persona.debate_stance,
          system_prompt: persona.system_prompt,
          // UI-only fields
          role: persona.perspective,
          personality: persona.persona_description,
          strengths: persona.key_strengths,
          avatar: persona.name.substring(0, 2).toUpperCase(),
          color: colors[index],
        };
      });

      setAgents(uiAgents);
      setSessionId(data.session_id);

      // 사용자가 에이전트를 확인하고 직접 "다음 단계" 버튼을 클릭하도록 Step 1에 유지

    } catch (err) {
      console.error("Failed to generate agents:", err);
      setError(err instanceof Error ? err.message : "에이전트 생성에 실패했습니다.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Run Round 1: Criteria Selection
  const runRound1 = async () => {
    if (!sessionId) return;
    setIsLoadingRound(true);
    console.log('[runRound1] Starting Round 1 for session:', sessionId);
    try {
      const response = await fetch(`/api/round/1`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sessionId }),
      });

      console.log('[runRound1] Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Round 1 API Error: ${response.status}`);
      }

      const result = await response.json();
      console.log("Round 1 completed - Raw result:", result);
      console.log("Round 1 debate turns:", result.data?.debate_turns);
      console.log("Round 1 final criteria:", result.data?.final_criteria);

      setRound1Data(result.data);
    } catch (err) {
      console.error("Failed to run Round 1:", err);
      setError(err instanceof Error ? err.message : "Round 1 실행에 실패했습니다.");
    } finally {
      setIsLoadingRound(false);
    }
  };

  // Run Round 2: AHP Weight Calculation
  const runRound2 = async () => {
    if (!sessionId) return;
    setIsLoadingRound(true);
    try {
      const response = await fetch(`/api/round/2`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sessionId }),
      });

      if (!response.ok) {
        throw new Error(`Round 2 API Error: ${response.status}`);
      }

      const result = await response.json();
      const data: Round2Result = result.data;
      setRound2Data(data);
      console.log("Round 2 completed:", data);
    } catch (err) {
      console.error("Failed to run Round 2:", err);
      setError(err instanceof Error ? err.message : "Round 2 실행에 실패했습니다.");
    } finally {
      setIsLoadingRound(false);
    }
  };

  // Run Round 3: Scoring Alternatives
  const runRound3 = async () => {
    if (!sessionId) return;
    setIsLoadingRound(true);
    try {
      const response = await fetch(`/api/round/3`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sessionId }),
      });

      if (!response.ok) {
        throw new Error(`Round 3 API Error: ${response.status}`);
      }

      const result = await response.json();
      const data: Round3Result = result.data;
      setRound3Data(data);
      console.log("Round 3 completed:", data);
    } catch (err) {
      console.error("Failed to run Round 3:", err);
      setError(err instanceof Error ? err.message : "Round 3 실행에 실패했습니다.");
    } finally {
      setIsLoadingRound(false);
    }
  };

  // Run Round 4: TOPSIS Final Ranking
  const runRound4 = async () => {
    if (!sessionId) return;
    setIsLoadingRound(true);
    try {
      const response = await fetch(`/api/round/4`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sessionId }),
      });

      if (!response.ok) {
        throw new Error(`Round 4 API Error: ${response.status}`);
      }

      const result = await response.json();
      const data: TOPSISResult = result.data;
      setRound4Data(data);
      console.log("Round 4 completed:", data);
    } catch (err) {
      console.error("Failed to run Round 4:", err);
      setError(err instanceof Error ? err.message : "Round 4 실행에 실패했습니다.");
    } finally {
      setIsLoadingRound(false);
    }
  };

  const hasAgents = agents.length > 0;

  const handleNextStep = async () => {
    if (currentStep === 2) {
      if (currentSubStep < conversationSubSteps.length) {
        // Move to next sub-step and trigger corresponding round
        const nextSubStep = currentSubStep + 1;
        setCurrentSubStep(nextSubStep);

        // Trigger Round 2 when moving to sub-step 2
        if (nextSubStep === 2 && !round2Data) {
          await runRound2();
        }
        // Trigger Round 3 when moving to sub-step 3
        else if (nextSubStep === 3 && !round3Data) {
          await runRound3();
        }
      } else {
        // Moving from step 2 to step 3 - trigger Round 4
        if (!round4Data) {
          await runRound4();
        }
        setCurrentStep(3);
        setCurrentSubStep(1);
      }
    } else if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePreviousStep = () => {
    if (currentStep === 2) {
      if (currentSubStep > 1) {
        setCurrentSubStep(currentSubStep - 1);
      } else {
        setCurrentStep(1);
      }
    } else if (currentStep === 3) {
      setCurrentStep(2);
      setCurrentSubStep(conversationSubSteps.length);
    } else if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = currentStep === 1 ? hasAgents : true;

  return (
    <div className="h-screen bg-[#101622] dark flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-[#282e39] px-6 sm:px-10 lg:px-20 py-4 flex-shrink-0">
        <div className="flex items-center gap-4 text-white">
          <div className="size-6 text-[#FF1F55]">
            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M36.7273 44C33.9891 44 31.6043 39.8386 30.3636 33.69C29.123 39.8386 26.7382 44 24 44C21.2618 44 18.877 39.8386 17.6364 33.69C16.3957 39.8386 14.0109 44 11.2727 44C7.25611 44 4 35.0457 4 24C4 12.9543 7.25611 4 11.2727 4C14.0109 4 16.3957 8.16144 17.6364 14.31C18.877 8.16144 21.2618 4 24 4C26.7382 4 29.123 8.16144 30.3636 14.31C31.6043 8.16144 33.9891 4 36.7273 4C40.7439 4 44 12.9543 44 24C44 35.0457 40.7439 44 36.7273 44Z"
                fill="currentColor"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold">AGORA</h2>
        </div>
      </header>

      {/* Step Navigator */}
      <StepNavigator
        currentStep={currentStep}
        totalSteps={3}
        steps={steps}
        onNext={handleNextStep}
        onPrevious={handlePreviousStep}
        canProceed={canProceed}
        subSteps={currentStep === 2 ? conversationSubSteps : undefined}
        currentSubStep={currentStep === 2 ? currentSubStep : undefined}
        onSubStepChange={setCurrentSubStep}
      />

      {/* Main Content */}
      {currentStep === 1 && (
        <main className="flex flex-1 flex-col lg:flex-row px-6 sm:px-10 lg:px-20 py-8 gap-8 overflow-hidden">
          {/* Left Panel - Input Section */}
          <div className="w-full lg:w-1/2 flex flex-col gap-6 overflow-y-auto">
            <div className="flex flex-col gap-3 flex-shrink-0">
              <h1 className="text-white text-4xl">에이전트 생성</h1>
              <p className="text-[#9ca6ba]">
                사용자의 핵심 정보를 자유 텍스트로 입력하고, 에이전트 생성을 클릭하면 에이전트가 생성됩니다.
              </p>
            </div>

            <UserInputForm
              interests={interests}
              aptitudes={aptitudes}
              pursuitValues={pursuitValues}
              candidateMajors={candidateMajors}
              onInterestsChange={setInterests}
              onAptitudesChange={setAptitudes}
              onPursuitValuesChange={setPursuitValues}
              onCandidateMajorsChange={setCandidateMajors}
              onGenerateAgents={generateAgents}
              isGenerating={isGenerating}
            />
          </div>

          {/* Right Panel - Agents Display */}
          <div className="w-full lg:w-1/2 rounded-xl bg-black/20 border border-[#282e39] p-8 overflow-y-auto">
            {!hasAgents && !isGenerating && (
              <div className="h-full flex items-center justify-center">
                <div className="text-center flex flex-col items-center gap-4">
                  <div className="flex items-center justify-center size-16 bg-[#FF1F55]/10 rounded-full">
                    <span className="material-symbols-outlined text-3xl text-[#FF1F55]">
                      smart_toy
                    </span>
                  </div>
                  <h3 className="text-xl text-white">생성된 에이전트가 여기에 표시됩니다</h3>
                  <p className="text-[#9ca6ba] max-w-sm">
                    왼쪽에 정보를 입력하고 에이전트 생성을 <br />
                    클릭하여 AI 에이전트를 만드세요.
                  </p>
                  {error && (
                    <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <p className="text-red-400 text-sm">{error}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {isGenerating && (
              <div className="h-full flex items-center justify-center">
                <div className="text-center flex flex-col items-center gap-4">
                  <div className="flex items-center justify-center size-16 bg-[#FF1F55]/10 rounded-full animate-pulse">
                    <span className="material-symbols-outlined text-3xl text-[#FF1F55]">
                      smart_toy
                    </span>
                  </div>
                  <h3 className="text-xl text-white">에이전트 생성 중...</h3>
                  <p className="text-[#9ca6ba]">
                    입력하신 정보를 바탕으로 고유한 AI 페르소나를 생성하고 있습니다
                  </p>
                </div>
              </div>
            )}

            {hasAgents && (
              <div className="w-full space-y-4">
                {agents.map((agent, index) => (
                  <AgentCard key={agent.id} agent={agent} index={index} />
                ))}
              </div>
            )}
          </div>
        </main>
      )}

      {currentStep === 2 && (
        <main className="flex flex-1 flex-col px-6 sm:px-10 lg:px-20 py-8 overflow-hidden">
          <AgentConversation
            agents={agents}
            currentSubStep={currentSubStep}
            candidateMajors={candidateMajors}
            round1Data={round1Data}
            round2Data={round2Data}
            round3Data={round3Data}
            isLoadingRound={isLoadingRound}
          />
        </main>
      )}

      {currentStep === 3 && (
        <main className="flex flex-1 flex-col px-6 sm:px-10 lg:px-20 py-8 overflow-hidden">
          <ReviewExport
            recommendations={round4Data?.final_ranking || mockRecommendations}
            candidateMajors={candidateMajors}
            agents={agents}
            criteriaWeights={round2Data?.criteria_weights}
            decisionMatrix={round3Data?.decision_matrix}
          />
        </main>
      )}
    </div>
  );
}
