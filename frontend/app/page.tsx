"use client";

import { useState } from "react";
import { UserInputForm } from "@/components/UserInputForm";
import { AgentCard } from "@/components/AgentCard";
import { StepNavigator } from "@/components/StepNavigator";
import { UIAgent } from "@/lib/types";
import { AgentConversation } from "@/components/AgentConversation";
import { ReviewExport } from "@/components/ReviewExport";

export default function App() {
  const [interests, setInterests] = useState("");
  const [aptitudes, setAptitudes] = useState("");
  const [pursuitValues, setPursuitValues] = useState("");
  const [candidateMajors, setCandidateMajors] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [agents, setAgents] = useState<UIAgent[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [currentSubStep, setCurrentSubStep] = useState(1);

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

  // Mock agent generation
  const generateAgents = async () => {
    setIsGenerating(true);
    setAgents([]);

    await new Promise((resolve) => setTimeout(resolve, 2000));

    const mockAgents: UIAgent[] = [
      {
        id: 1,
        name: "Nova",
        perspective: "창의적 혁신",
        persona_description: `${interests.split(",")[0]?.trim() || "창의적 활동"}과 혁신적 문제해결을 결합하는 비전 있는 사상가입니다.`,
        key_strengths: ["아이디어 발상", "전략적 사고", "창의적 솔루션"],
        debate_stance: "혁신과 창의성을 통한 문제 해결을 중시합니다.",
        system_prompt: "",
        role: "창의적 혁신가",
        personality: `${interests.split(",")[0]?.trim() || "창의적 활동"}과 혁신적 문제해결을 결합하는 비전 있는 사상가입니다.`,
        strengths: ["아이디어 발상", "전략적 사고", "창의적 솔루션"],
        avatar: "NV",
        color: "bg-gradient-to-br from-cyan-500 to-blue-600",
      },
      {
        id: 2,
        name: "Atlas",
        perspective: "분석적 전략",
        persona_description: `${aptitudes.split(",")[0]?.trim() || "분석적 사고"}에 뛰어난 체계적인 분석가입니다.`,
        key_strengths: ["데이터 분석", "비판적 사고", "패턴 인식"],
        debate_stance: "객관적 데이터와 논리적 분석을 중시합니다.",
        system_prompt: "",
        role: "분석적 전략가",
        personality: `${aptitudes.split(",")[0]?.trim() || "분석적 사고"}에 뛰어난 체계적인 분석가입니다.`,
        strengths: ["데이터 분석", "비판적 사고", "패턴 인식"],
        avatar: "AT",
        color: "bg-gradient-to-br from-emerald-500 to-teal-600",
      },
      {
        id: 3,
        name: "Echo",
        perspective: "공감적 협력",
        persona_description: `${pursuitValues.split(",")[0]?.trim() || "협업"}을 중시하는 사람 중심의 커뮤니케이터입니다.`,
        key_strengths: ["소통", "공감", "팀 빌딩"],
        debate_stance: "인간 중심의 가치와 지속가능성을 중시합니다.",
        system_prompt: "",
        role: "공감적 협력자",
        personality: `${pursuitValues.split(",")[0]?.trim() || "협업"}을 중시하는 사람 중심의 커뮤니케이터입니다.`,
        strengths: ["소통", "공감", "팀 빌딩"],
        avatar: "EC",
        color: "bg-gradient-to-br from-amber-500 to-orange-600",
      },
    ];

    setAgents(mockAgents);
    setIsGenerating(false);
  };

  const hasAgents = agents.length > 0;

  const handleNextStep = () => {
    if (currentStep === 2) {
      if (currentSubStep < conversationSubSteps.length) {
        setCurrentSubStep(currentSubStep + 1);
      } else {
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
          <h2 className="text-xl">Agent Conversation</h2>
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
          />
        </main>
      )}

      {currentStep === 3 && (
        <main className="flex flex-1 flex-col px-6 sm:px-10 lg:px-20 py-8 overflow-hidden">
          <ReviewExport
            recommendations={mockRecommendations}
            candidateMajors={candidateMajors}
            agents={agents}
          />
        </main>
      )}
    </div>
  );
}
