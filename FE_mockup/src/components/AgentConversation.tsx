import { Agent } from "./AgentCard";
import { useState, useEffect, useRef } from "react";
import { CheckCircle2 } from "lucide-react";

interface Message {
  id: number;
  agentId: number;
  agentName: string;
  agentAvatar: string;
  agentColor: string;
  content: string;
  timestamp: string;
}

interface AgentConversationProps {
  agents: Agent[];
  candidateMajors: string[];
  currentSubStep: number;
}

export function AgentConversation({
  agents,
  candidateMajors,
  currentSubStep,
}: AgentConversationProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [typingAgentId, setTypingAgentId] = useState<number | null>(null);
  const [isConversationComplete, setIsConversationComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Mock conversation data based on sub-step
  const getConversationForSubStep = (subStep: number): Message[] => {
    const majorsText = candidateMajors.length > 0 
      ? candidateMajors.join(", ") 
      : "컴퓨터공학, 데이터사이언스, 철학";

    // Round 1: Criteria Selection
    const criteriaSelectionMessages: Message[] = [
      {
        id: 1,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: `환영합니다. 오늘 우리는 사용자가 선택한 전공들(${majorsText})을 평가할 기준을 수립할 것입니다. 여러분의 관점에서 중요한 평가 기준을 제안해주세요.`,
        timestamp: "10:00 AM",
      },
      {
        id: 2,
        agentId: 1,
        agentName: agents[0]?.name || "Nova",
        agentAvatar: agents[0]?.avatar || "NV",
        agentColor: agents[0]?.color || "bg-gradient-to-br from-cyan-500 to-blue-600",
        content: "저는 첫 번째 기준으로 '혁신 잠재력 및 창의적 표현'을 제안합니다. 각 전공이 새로운 아이디어를 실현할 수 있는 환경을 얼마나 제공하는지 평가하는 것이 중요합니다.",
        timestamp: "10:02 AM",
      },
      {
        id: 3,
        agentId: 2,
        agentName: agents[1]?.name || "Atlas",
        agentAvatar: agents[1]?.avatar || "AT",
        agentColor: agents[1]?.color || "bg-gradient-to-br from-emerald-500 to-teal-600",
        content: "저는 '경제적 성장 잠재력'을 제안합니다. 졸업 후 예상 연봉, 취업률, 산업 성장률 등 객관적 지표가 필요합니다.",
        timestamp: "10:04 AM",
      },
      {
        id: 4,
        agentId: 3,
        agentName: agents[2]?.name || "Echo",
        agentAvatar: agents[2]?.avatar || "EC",
        agentColor: agents[2]?.color || "bg-gradient-to-br from-amber-500 to-orange-600",
        content: "'워라밸과 지속 가능한 커리어 발전'도 중요합니다. 사용자가 장기적으로 행복하게 일할 수 있는지 평가해야 합니다.",
        timestamp: "10:06 AM",
      },
      {
        id: 5,
        agentId: 1,
        agentName: agents[0]?.name || "Nova",
        agentAvatar: agents[0]?.avatar || "NV",
        agentColor: agents[0]?.color || "bg-gradient-to-br from-cyan-500 to-blue-600",
        content: "'사회적 영향력과 의미 있는 기여'를 추가하고 싶습니다. 이 전공이 세상에 긍정적인 변화를 만들 수 있는지가 중요합니다.",
        timestamp: "10:08 AM",
      },
      {
        id: 6,
        agentId: 2,
        agentName: agents[1]?.name || "Atlas",
        agentAvatar: agents[1]?.avatar || "AT",
        agentColor: agents[1]?.color || "bg-gradient-to-br from-emerald-500 to-teal-600",
        content: "좋습니다. 마지막으로 '개인 적성 및 흥미 일치도'를 제안합니다. 사용자의 입력 데이터가 각 전공의 요구 역량과 얼마나 일치하는지 분석해야 합니다.",
        timestamp: "10:10 AM",
      },
      {
        id: 7,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: "훌륭합니다. 5가지 평가 기준이 선정되었습니다:\n\n1. 혁신 잠재력 및 창의성\n2. 경제적 성장 잠재력\n3. 워라밸 & 지속가능성\n4. 사회적 영향력\n5. 개인 적성 일치도\n\n이 기준들은 다양한 관점을 균형 있게 반영하고 있습니다.",
        timestamp: "10:12 AM",
      },
    ];

    // Round 2: Weight Calculation (AHP)
    const weightCalculationMessages: Message[] = [
      {
        id: 1,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: "이제 선정된 5개 기준의 상대적 중요도를 계산하겠습니다. AHP 방법론을 사용하여 각 기준 쌍을 비교할 것입니다. 먼저 '경제적 성장 잠재력' 대 '혁신 잠재력'을 비교해봅시다.",
        timestamp: "10:20 AM",
      },
      {
        id: 2,
        agentId: 1,
        agentName: agents[0]?.name || "Nova",
        agentAvatar: agents[0]?.avatar || "NV",
        agentColor: agents[0]?.color || "bg-gradient-to-br from-cyan-500 to-blue-600",
        content: "저는 혁신 잠재력이 더 중요하다고 봅니다. 경제적 보상은 혁신의 결과로 따라오는 것이지 목표 자체가 아닙니다. 혁신 쪽에 7:3 정도의 비율이 적절해 보입니다.",
        timestamp: "10:22 AM",
      },
      {
        id: 3,
        agentId: 2,
        agentName: agents[1]?.name || "Atlas",
        agentAvatar: agents[1]?.avatar || "AT",
        agentColor: agents[1]?.color || "bg-gradient-to-br from-emerald-500 to-teal-600",
        content: "동의할 수 없습니다. 사용자가 입력 데이터에서 '높은 연봉'과 '빠른 커리어 성장'을 명시적으로 언급했습니다. 경제적 성장이 60%, 혁신이 40% 가중치를 가져야 합니다.",
        timestamp: "10:24 AM",
      },
      {
        id: 4,
        agentId: 3,
        agentName: agents[2]?.name || "Echo",
        agentAvatar: agents[2]?.avatar || "EC",
        agentColor: agents[2]?.color || "bg-gradient-to-br from-amber-500 to-orange-600",
        content: "두 기준 모두 중요하지만, 사용자가 워라밸도 중시한다는 점을 고려하면 극단적인 경제 추구는 부적절합니다. 5:5의 균형 잡힌 비율을 제안합니다.",
        timestamp: "10:26 AM",
      },
      {
        id: 5,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: "세 의견을 종합하여, 경제적 성장 55%, 혁신 45%로 결정하겠습니다. 다음 비교로 넘어갑니다...\n\n[9개 비교 진행 중...]",
        timestamp: "10:28 AM",
      },
      {
        id: 6,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: "✅ AHP 분석 완료!\n\n최종 가중치:\n• 경제적 성장 잠재력: 32.5%\n• 개인 적성 일치도: 24.8%\n• 워라밸 & 지속가능성: 18.3%\n• 혁신 잠재력: 14.2%\n• 사회적 영향력: 10.2%\n\n일관성 비율(CR): 0.0214 ✓ (기준: <0.1)",
        timestamp: "10:35 AM",
      },
    ];

    // Round 3: Major Scoring
    const scoringMessages: Message[] = [
      {
        id: 1,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: `이제 각 전공을 5개 기준에 대해 평가하겠습니다. 먼저 '${candidateMajors[0] || "컴퓨터공학"}'의 '경제적 성장 잠재력'을 평가해주세요.`,
        timestamp: "10:40 AM",
      },
      {
        id: 2,
        agentId: 2,
        agentName: agents[1]?.name || "Atlas",
        agentAvatar: agents[1]?.avatar || "AT",
        agentColor: agents[1]?.color || "bg-gradient-to-br from-emerald-500 to-teal-600",
        content: `${candidateMajors[0] || "컴퓨터공학"}의 경제적 전망은 매우 우수합니다. 2024년 기준 초봉 평균 $75K, 5년차 평균 $110K입니다. 취업률 92.3%, IT 산업 연평균 성장률 8.2%를 고려하면 10점 만점에 9점을 부여합니다.`,
        timestamp: "10:42 AM",
      },
      {
        id: 3,
        agentId: 1,
        agentName: agents[0]?.name || "Nova",
        agentAvatar: agents[0]?.avatar || "NV",
        agentColor: agents[0]?.color || "bg-gradient-to-br from-cyan-500 to-blue-600",
        content: "동의합니다. 다만 최근 AI 붐으로 인한 과열 가능성을 고려하면 9점이 적절합니다.",
        timestamp: "10:44 AM",
      },
      {
        id: 4,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: `${candidateMajors[0] || "컴퓨터공학"} - 경제적 성장: 9점 확정.\n\n다음으로 '개인 적성 일치도'를 평가합니다.`,
        timestamp: "10:45 AM",
      },
      {
        id: 5,
        agentId: 3,
        agentName: agents[2]?.name || "Echo",
        agentAvatar: agents[2]?.avatar || "EC",
        agentColor: agents[2]?.color || "bg-gradient-to-br from-amber-500 to-orange-600",
        content: "사용자가 '논리적 사고력'과 '코딩 능력'을 강점으로 언급했고, '수학 경시대회 입상 경력'도 있습니다. 컴퓨터공학과의 일치도는 매우 높아 9.5점을 부여합니다.",
        timestamp: "10:47 AM",
      },
      {
        id: 6,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: `[평가 진행 중...]\n\n현재까지: ${candidateMajors.length || 3}개 전공 × 5개 기준 = ${(candidateMajors.length || 3) * 5}개 평가 완료`,
        timestamp: "10:55 AM",
      },
      {
        id: 7,
        agentId: 0,
        agentName: "Director",
        agentAvatar: "DR",
        agentColor: "bg-gradient-to-br from-purple-500 to-purple-700",
        content: `✅ 의사결정 매트릭스 완성!\n\n전공별 점수 요약:\n• ${candidateMajors[0] || "컴퓨터공학"}: 경제 9.0, 적성 9.5, 워라밸 6.5, 혁신 8.5, 사회 7.0\n• ${candidateMajors[1] || "데이터사이언스"}: 경제 8.5, 적성 8.0, 워라밸 6.0, 혁신 9.0, 사회 8.5\n• ${candidateMajors[2] || "철학"}: 경제 4.0, 적성 7.5, 워라밸 8.5, 혁신 7.0, 사회 9.0\n\n다음 단계에서 TOPSIS를 통해 최종 순위를 도출합니다.`,
        timestamp: "11:00 AM",
      },
    ];

    switch (subStep) {
      case 1:
        return criteriaSelectionMessages;
      case 2:
        return weightCalculationMessages;
      case 3:
        return scoringMessages;
      default:
        return [];
    }
  };

  // Load messages when substep changes
  useEffect(() => {
    const conversation = getConversationForSubStep(currentSubStep);
    setMessages([]);
    setCurrentMessageIndex(0);
    setTypingAgentId(null);
    setIsConversationComplete(false);

    // Animate messages
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => {
        if (prev < conversation.length) {
          const nextMessage = conversation[prev];
          setTypingAgentId(nextMessage.agentId);
          setMessages((msgs) => [...msgs, nextMessage]);

          // Stop typing indicator after a delay
          setTimeout(() => {
            setTypingAgentId(null);
          }, 500);

          return prev + 1;
        } else {
          clearInterval(interval);
          setIsConversationComplete(true);
          return prev;
        }
      });
    }, 1500); // New message every 1.5 seconds

    return () => clearInterval(interval);
  }, [currentSubStep, agents, candidateMajors]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const renderInfoPanel = () => {
    const majors = candidateMajors.length > 0 
      ? candidateMajors 
      : ["컴퓨터공학", "데이터사이언스", "철학"];

    if (currentSubStep === 1) {
      // Round 1: Criteria Selection
      const criteria = [
        { name: "혁신 잠재력 및 창의성", status: "confirmed" },
        { name: "경제적 성장 잠재력", status: "confirmed" },
        { name: "워라밸 & 지속가능성", status: "confirmed" },
        { name: "사회적 영향력", status: "confirmed" },
        { name: "개인 적성 일치도", status: "confirmed" },
      ];

      return (
        <div className="bg-black/20 border border-[#282e39] rounded-lg p-6 h-full overflow-y-auto">
          <h3 className="text-white mb-4">선정된 평가 기준</h3>
          <div className="space-y-3">
            {criteria.map((item, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-[#1b1f27] border border-[#282e39] rounded-lg"
              >
                <CheckCircle2 className="size-5 text-green-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-white">{item.name}</p>
                  <p className="text-[#9ca6ba] text-sm mt-1">
                    상태: <span className="text-green-400">확정</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
            <p className="text-purple-300 text-sm">
              ✓ 5개 기준 모두 다중 에이전트 합의를 통해 확정되었습니다
            </p>
          </div>
        </div>
      );
    } else if (currentSubStep === 2) {
      // Round 2: AHP Weighting
      const weights = [
        { name: "경제적 성장", weight: 32.5, color: "bg-[#FF1F55]" },
        { name: "개인 적성", weight: 24.8, color: "bg-[#FF4572]" },
        { name: "워라밸", weight: 18.3, color: "bg-purple-500" },
        { name: "혁신 잠재력", weight: 14.2, color: "bg-blue-500" },
        { name: "사회적 영향", weight: 10.2, color: "bg-green-500" },
      ];

      const maxWeight = Math.max(...weights.map((w) => w.weight));

      return (
        <div className="bg-black/20 border border-[#282e39] rounded-lg p-6 h-full overflow-y-auto">
          <h3 className="text-white mb-4">AHP 가중치 분포</h3>
          <div className="space-y-4 mb-6">
            {weights.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm">{item.name}</span>
                  <span className="text-[#FF1F55]">{item.weight}%</span>
                </div>
                <div className="h-8 bg-[#1b1f27] rounded-lg overflow-hidden relative">
                  <div
                    className={`${item.color} h-full transition-all duration-1000 flex items-center justify-end pr-3`}
                    style={{ width: `${(item.weight / maxWeight) * 100}%` }}
                  >
                    <span className="text-white text-xs"></span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p className="text-green-300 text-sm">
              ✓ 일관성 비율(CR): 0.0214
            </p>
            <p className="text-[#9ca6ba] text-xs mt-1">
              CR &lt; 0.1은 허용 가능한 일관성을 나타냅니다
            </p>
          </div>
        </div>
      );
    } else if (currentSubStep === 3) {
      // Round 3: Decision Matrix
      const decisionMatrix = [
        {
          major: majors[0] || "컴퓨터공학",
          scores: { economic: 9.0, aptitude: 9.5, balance: 6.5, innovation: 8.5, social: 7.0 },
        },
        {
          major: majors[1] || "데이터사이언스",
          scores: { economic: 8.5, aptitude: 8.0, balance: 6.0, innovation: 9.0, social: 8.5 },
        },
        {
          major: majors[2] || "철학",
          scores: { economic: 4.0, aptitude: 7.5, balance: 8.5, innovation: 7.0, social: 9.0 },
        },
      ];

      return (
        <div className="bg-black/20 border border-[#282e39] rounded-lg p-6 h-full overflow-y-auto">
          <h3 className="text-white mb-4">의사결정 매트릭스</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#282e39]">
                  <th className="text-left text-[#9ca6ba] pb-2">전공</th>
                  <th className="text-center text-[#9ca6ba] px-2 pb-2">경제</th>
                  <th className="text-center text-[#9ca6ba] px-2 pb-2">적성</th>
                  <th className="text-center text-[#9ca6ba] px-2 pb-2">워라밸</th>
                  <th className="text-center text-[#9ca6ba] px-2 pb-2">혁신</th>
                  <th className="text-center text-[#9ca6ba] px-2 pb-2">사회</th>
                </tr>
              </thead>
              <tbody>
                {decisionMatrix.map((row, index) => (
                  <tr key={index} className="border-b border-[#282e39]/50">
                    <td className="text-white py-3">{row.major}</td>
                    <td className="text-center text-[#d1d5db] py-3">{row.scores.economic}</td>
                    <td className="text-center text-[#d1d5db] py-3">{row.scores.aptitude}</td>
                    <td className="text-center text-[#d1d5db] py-3">{row.scores.balance}</td>
                    <td className="text-center text-[#d1d5db] py-3">{row.scores.innovation}</td>
                    <td className="text-center text-[#d1d5db] py-3">{row.scores.social}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-blue-300 text-sm">
              ✓ {majors.length}개 전공 × 5개 기준 = 총 {majors.length * 5}개 평가
            </p>
            <p className="text-[#9ca6ba] text-xs mt-1">
              TOPSIS 순위 계산 준비 완료
            </p>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex gap-6 h-full overflow-hidden">
      {/* Left Side - Agent Cards */}
      <div className="w-80 flex flex-col gap-4 overflow-y-auto">
        {/* Director Card */}
        <div
          className={`bg-black/20 border rounded-lg p-4 transition-all duration-300 ${
            typingAgentId === 0
              ? "border-purple-500 shadow-lg shadow-purple-500/20"
              : "border-[#282e39]"
          }`}
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center size-12 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 text-white">
              <span>DR</span>
            </div>
            <div className="flex-1">
              <h3 className="text-white">Director</h3>
              <p className="text-[#9ca6ba] text-xs">Moderator</p>
            </div>
          </div>
          <p className="text-[#9ca6ba] text-sm">
            토론을 진행하고 에이전트들의 의견을 종합하여 합의를 이끌어냅니다.
          </p>
        </div>

        {/* Agent Cards */}
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={`bg-black/20 border rounded-lg p-4 transition-all duration-300 ${
              typingAgentId === agent.id
                ? "border-[#FF1F55] shadow-lg shadow-[#FF1F55]/20"
                : "border-[#282e39]"
            }`}
          >
            <div className="flex items-center gap-3 mb-3">
              <div
                className={`flex items-center justify-center size-12 rounded-full ${agent.color} text-white`}
              >
                <span>{agent.avatar}</span>
              </div>
              <div className="flex-1">
                <h3 className="text-white">{agent.name}</h3>
                <p className="text-[#9ca6ba] text-xs">{agent.role}</p>
              </div>
            </div>
            <p className="text-[#9ca6ba] text-sm">{agent.personality}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {agent.strengths.map((strength, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-[#9ca6ba]"
                >
                  {strength}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Center - Conversation */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((msg) => {
            const agent = agents.find((a) => a.id === msg.agentId);
            const isDirector = msg.agentId === 0;

            return (
              <div
                key={msg.id}
                className="flex gap-3"
              >
                {/* Avatar */}
                <div
                  className={`flex items-center justify-center size-10 rounded-full ${msg.agentColor} text-white flex-shrink-0`}
                >
                  <span className="text-sm">{msg.agentAvatar}</span>
                </div>

                {/* Message Content */}
                <div className="flex-1 max-w-2xl">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-white">{msg.agentName}</span>
                    <span className="text-[#9ca6ba] text-xs">{msg.timestamp}</span>
                  </div>
                  <div
                    className={`p-4 rounded-lg ${
                      isDirector
                        ? "bg-gradient-to-r from-purple-500/20 to-purple-700/20 border border-purple-500/30"
                        : "bg-[#1b1f27] border border-[#282e39]"
                    }`}
                  >
                    <p className="text-white whitespace-pre-line">{msg.content}</p>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {typingAgentId !== null && (
            <div className="flex gap-3">
              <div
                className={`flex items-center justify-center size-10 rounded-full ${
                  typingAgentId === 0
                    ? "bg-gradient-to-br from-purple-500 to-purple-700"
                    : agents.find((a) => a.id === typingAgentId)?.color || "bg-gray-500"
                } text-white flex-shrink-0`}
              >
                <span className="text-sm">
                  {typingAgentId === 0
                    ? "DR"
                    : agents.find((a) => a.id === typingAgentId)?.avatar || "?"}
                </span>
              </div>
              <div className="flex-1 max-w-2xl">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-white">
                    {typingAgentId === 0
                      ? "Director"
                      : agents.find((a) => a.id === typingAgentId)?.name || "Agent"}
                  </span>
                </div>
                <div className="p-4 rounded-lg bg-[#1b1f27] border border-[#282e39]">
                  <div className="flex gap-1">
                    <span className="size-2 bg-[#9ca6ba] rounded-full animate-bounce" />
                    <span
                      className="size-2 bg-[#9ca6ba] rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                    <span
                      className="size-2 bg-[#9ca6ba] rounded-full animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Right Side - Info Panel (only shown when conversation is complete) */}
      {isConversationComplete && (
        <div className="w-80 flex-shrink-0 animate-in fade-in slide-in-from-right duration-500">
          {renderInfoPanel()}
        </div>
      )}
    </div>
  );
}