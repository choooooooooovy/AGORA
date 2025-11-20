"use client";

import { Card, CardContent } from "./ui/card";
import { UIAgent, Round1Result, Round2Result, Round3Result, SelectedCriterion, Message } from "@/lib/types";
import { useState, useEffect, useRef } from "react";

interface AgentConversationProps {
  agents: UIAgent[];
  candidateMajors: string[];
  currentSubStep: number;
  round1Data: Round1Result | null;
  round2Data: Round2Result | null;
  round3Data: Round3Result | null;
  isLoadingRound: boolean;
}

export function AgentConversation({
  agents,
  currentSubStep,
  round1Data,
  round2Data,
  round3Data,
  isLoadingRound,
}: AgentConversationProps) {
  const [displayedMessages, setDisplayedMessages] = useState<Message[]>([]);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [totalMessages, setTotalMessages] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const allMessagesRef = useRef<Message[]>([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Process debate data when round data changes
  useEffect(() => {
    let debateData = null;

    console.log('[AgentConversation] currentSubStep:', currentSubStep);
    console.log('[AgentConversation] round1Data:', round1Data);
    console.log('[AgentConversation] agents:', agents);

    if (currentSubStep === 1 && round1Data) {
      debateData = round1Data.round1_debate_turns;
      console.log('[AgentConversation] Round 1 debate data:', debateData);
    } else if (currentSubStep === 2 && round2Data) {
      debateData = round2Data.round2_debate_turns;
    } else if (currentSubStep === 3 && round3Data) {
      debateData = round3Data.round3_debate_turns;
    }

    if (debateData && debateData.length > 0) {
      // Convert DebateTurn[] to Message[]
      const convertedMessages: Message[] = debateData.map((turn, index) => {
        const agent = agents.find(a => a.name === turn.speaker);
        const isDirector = turn.speaker === "Director";

        // Clean content
        let cleanContent = turn.content;

        // Round 2: Agent의 comparison_matrix JSON 파싱
        if (!isDirector && turn.content.includes('"comparison_matrix"')) {
          try {
            const jsonMatch = turn.content.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
              const parsed = JSON.parse(jsonMatch[1]);
              const matrix = parsed.comparison_matrix;

              // 설명 텍스트 추출 (JSON 블록 전 부분)
              const explanationText = turn.content.substring(0, turn.content.indexOf('```json')).trim();

              // 테이블 형태로 변환
              let tableContent = '\n\n**📊 쌍대비교 결과:**\n\n';
              Object.entries(matrix).forEach(([pair, score]) => {
                tableContent += `• ${pair}: **${score}점**\n`;
              });

              cleanContent = explanationText + tableContent;
            }
          } catch (e) {
            console.error('Failed to parse comparison_matrix:', e);
          }
        }

        // Director의 final_decision 타입 메시지는 JSON 파싱하여 구조화
        if (isDirector && turn.type === "final_decision") {
          try {
            const parsed = JSON.parse(turn.content);

            // Round 1: selected_criteria와 summary
            if (parsed.summary && parsed.selected_criteria) {
              cleanContent = `📋 **최종 결정**\n\n${parsed.summary}`;
            }
            // Round 2: comparison_matrix와 reasoning
            else if (parsed.comparison_matrix && parsed.reasoning) {
              let formattedContent = '✅ **AHP 분석 완료**\n\n';

              // Comparison matrix를 테이블로
              formattedContent += '**📊 최종 쌍대비교 점수:**\n\n';
              Object.entries(parsed.comparison_matrix).forEach(([pair, score]) => {
                formattedContent += `• ${pair}: **${score}점**\n`;
              });

              // Reasoning을 그대로 표시
              formattedContent += '\n**💡 결정 근거:**\n\n';
              formattedContent += parsed.reasoning;

              cleanContent = formattedContent;
            }
          } catch (e) {
            console.error('Failed to parse final_decision:', e);
            // JSON 파싱 실패시 원본 유지
          }
        }

        cleanContent = cleanContent.replace(/^---\n/, '').replace(/\n---$/, '');
        cleanContent = cleanContent.trim();

        // 에이전트를 찾지 못한 경우 이름 기반으로 기본 색상/아바타 할당
        let agentAvatar = "??";
        let agentColor = "bg-gradient-to-br from-gray-500 to-gray-700";

        if (isDirector) {
          agentAvatar = "DR";
          agentColor = "bg-gradient-to-br from-purple-500 to-purple-700";
        } else if (agent) {
          agentAvatar = agent.avatar;
          agentColor = agent.color;
        } else {
          // 에이전트를 찾지 못한 경우 이름의 첫 2글자로 아바타 생성
          agentAvatar = turn.speaker.substring(0, 2).toUpperCase();
          // 이름 기반으로 색상 할당
          const colors = [
            "bg-gradient-to-br from-blue-500 to-blue-700",
            "bg-gradient-to-br from-green-500 to-green-700",
            "bg-gradient-to-br from-orange-500 to-orange-700",
            "bg-gradient-to-br from-cyan-500 to-cyan-700",
            "bg-gradient-to-br from-pink-500 to-pink-700",
          ];
          const colorIndex = turn.speaker.charCodeAt(0) % colors.length;
          agentColor = colors[colorIndex];
        }

        return {
          id: index + 1,
          agentId: isDirector ? 0 : (agent?.id || -1),
          agentName: turn.speaker,
          agentAvatar,
          agentColor,
          content: cleanContent,
          timestamp: new Date(turn.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          }),
          type: turn.type as Message['type'],
        };
      });

      console.log('[AgentConversation] Converted messages:', convertedMessages.length);
      allMessagesRef.current = convertedMessages;

      // 메시지 초기화 및 애니메이션 시작
      if (convertedMessages.length > 0) {
        // 첫 번째 메시지는 즉시 표시
        setDisplayedMessages([convertedMessages[0]]);
        setCurrentMessageIndex(1); // 다음 메시지부터 시작
        setTotalMessages(convertedMessages.length);
      }
    } else {
      console.log('[AgentConversation] No debate data found');
      allMessagesRef.current = [];
      setDisplayedMessages([]);
      setCurrentMessageIndex(0);
      setTotalMessages(0);
    }
  }, [currentSubStep, round1Data, round2Data, round3Data, agents]);

  // Animate messages appearing one by one
  useEffect(() => {
    if (currentMessageIndex === 0 || currentMessageIndex >= allMessagesRef.current.length) {
      console.log('[AgentConversation] Animation stopped. Index:', currentMessageIndex, 'Total:', allMessagesRef.current.length);
      return;
    }

    console.log('[AgentConversation] Setting timer for message', currentMessageIndex);
    const timer = setTimeout(() => {
      console.log('[AgentConversation] Displaying message', currentMessageIndex);
      setDisplayedMessages(prev => [
        ...prev,
        allMessagesRef.current[currentMessageIndex]
      ]);
      setCurrentMessageIndex(prev => prev + 1);
    }, 7000); // 7 seconds between messages

    return () => clearTimeout(timer);
  }, [currentMessageIndex]);

  // Scroll when new message appears
  useEffect(() => {
    scrollToBottom();
  }, [displayedMessages.length]);

  const getRoundTitle = () => {
    switch (currentSubStep) {
      case 1:
        return "Round 1: 평가 기준 선택";
      case 2:
        return "Round 2: 기준 가중치 산출 (AHP)";
      case 3:
        return "Round 3: 대안(학과)간 평가";
      default:
        return "에이전트 대화";
    }
  };

  return (
    <div className="flex flex-1 gap-6 overflow-hidden">
      {/* Left Sidebar - Agent Cards */}
      <div className="w-80 shrink-0 space-y-3 overflow-y-auto">
        {/* Director Card */}
        <Card className="bg-[#0a0d12] border-[#3b4354] py-2">
          <CardContent className="p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-purple-700 text-white font-semibold">
                DR
              </div>
              <div>
                <h3 className="font-semibold text-white">Director</h3>
                <p className="text-xs text-[#9ca6ba]">Moderator</p>
              </div>
            </div>
            <p className="mt-2 text-sm text-[#9ca6ba] leading-relaxed">
              토론을 진행하고 에이전트들의 의견을 종합하여 합의를 이끌어냅니다.
            </p>
          </CardContent>
        </Card>

        {/* Agent Cards */}
        {agents.map((agent) => (
          <Card key={agent.id} className="bg-[#0a0d12] border-[#3b4354] py-2">
            <CardContent className="p-3">
              <div className="flex items-center gap-3">
                <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${agent.color} text-white font-semibold`}>
                  {agent.avatar}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-white truncate">{agent.name}</h3>
                  <p className="text-xs text-[#9ca6ba] truncate">{agent.perspective}</p>
                </div>
              </div>
              <p className="mt-2 text-sm text-[#9ca6ba] leading-relaxed">
                {agent.personality}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {agent.strengths.slice(0, 3).map((strength, idx) => (
                  <span
                    key={idx}
                    className="rounded-full bg-[#282e39] px-2 py-1 text-xs text-[#9ca6ba]"
                  >
                    {strength}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Conversation Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-white">{getRoundTitle()}</h2>
          <p className="text-sm text-[#9ca6ba] mt-1">
            {currentSubStep === 1 && "에이전트들이 전공 평가 기준을 논의하고 있습니다"}
            {currentSubStep === 2 && "각 기준의 중요도를 AHP 방법으로 산정하고 있습니다"}
            {currentSubStep === 3 && "선정된 기준으로 전공들을 평가하고 있습니다"}
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto rounded-lg border border-[#282e39] bg-black/20 p-6">
          {(isLoadingRound || (displayedMessages.length === 0 && totalMessages === 0)) && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mb-4 inline-block h-12 w-12 animate-spin rounded-full border-4 border-[#FF1F55] border-t-transparent"></div>
                <p className="text-[#9ca6ba]">에이전트들이 토론 중입니다...</p>
              </div>
            </div>
          )}

          {displayedMessages.map((msg) => (
            <div key={msg.id} className="flex gap-3 animate-fadeIn">
              {/* Agent Avatar */}
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${msg.agentColor} text-sm font-semibold text-white`}
              >
                {msg.agentAvatar}
              </div>

              {/* Message Content */}
              <div className="flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="font-semibold text-white">{msg.agentName}</span>
                  <span className="text-xs text-[#9ca6ba]">{msg.timestamp}</span>
                </div>
                <div
                  className={`mt-2 rounded-lg p-3 ${msg.agentName === "Director"
                    ? "border border-purple-500/30 bg-purple-500/10"
                    : "border border-[#3b4354] bg-[#1b1f27]"
                    }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#e5e7eb]">
                    {msg.content}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {currentMessageIndex < totalMessages && (
            <div className="flex gap-3 opacity-50">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center">
                <div className="h-2 w-2 animate-pulse rounded-full bg-[#FF1F55]"></div>
              </div>
              <p className="text-sm text-[#9ca6ba] pt-2">입력 중...</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Right Panel - Round Results */}
      <div className="w-80 shrink-0">
        <Card className="h-full overflow-y-auto bg-[#0a0d12] border-[#3b4354] py-0">
          <CardContent className="p-4">
            <h3 className="mb-3 text-lg font-semibold text-white">
              {currentSubStep === 1 && "선정된 평가 기준"}
              {currentSubStep === 2 && "AHP 가중치"}
              {currentSubStep === 3 && "의사결정 매트릭스"}
            </h3>

            {/* Round 1: Selected Criteria - Only show after Director's final decision is displayed */}
            {currentSubStep === 1 && round1Data && round1Data.round1_director_decision && round1Data.round1_director_decision.selected_criteria &&
              displayedMessages.some(msg => msg.type === 'final_decision') && (
                <div className="space-y-2">
                  {round1Data.round1_director_decision.selected_criteria.map((criterion: SelectedCriterion, index: number) => (
                    <div
                      key={index}
                      className="rounded-lg border border-[#3b4354] bg-[#1b1f27] p-2.5"
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 shrink-0">✓</span>
                        <div className="flex-1">
                          <p className="font-semibold text-white text-base leading-snug">{criterion.name}</p>
                          <p className="mt-1 text-xs text-[#9ca6ba] leading-relaxed">{criterion.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  {round1Data.round1_director_decision.selected_criteria.length > 0 && (
                    <div className="mt-3 rounded-lg border border-purple-500/30 bg-purple-500/10 p-2.5">
                      <p className="text-xs text-purple-300">
                        ✓ {round1Data.round1_director_decision.selected_criteria.length}개 기준 모두 에이전트 합의를 통해 선정되었습니다
                      </p>
                    </div>
                  )}
                </div>
              )}

            {/* Round 1: Loading or No Data */}
            {currentSubStep === 1 && !round1Data && (
              <div className="text-center py-8">
                <p className="text-sm text-[#9ca6ba]">토론 진행 중...</p>
              </div>
            )}

            {/* Round 2: AHP Weights - Only show after Director's final decision is displayed */}
            {currentSubStep === 2 && round2Data &&
              displayedMessages.some(msg => msg.type === 'final_decision') && (
                <div className="space-y-4">
                  {Object.entries(round2Data.criteria_weights)
                    .sort(([, a], [, b]) => b - a) // Sort by weight descending
                    .map(([criterion, weight], index) => {
                      const colors = ['#EF4444', '#EC4899', '#A855F7', '#3B82F6', '#10B981'];
                      const color = colors[index % colors.length];

                      return (
                        <div key={index}>
                          <div className="mb-1 flex items-center justify-between text-sm">
                            <span className="text-white">{criterion}</span>
                            <span className="font-semibold" style={{ color }}>
                              {(weight * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-[#1b1f27]">
                            <div
                              className="h-full transition-all duration-500 rounded-full"
                              style={{
                                width: `${weight * 100}%`,
                                backgroundColor: color
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  <div className="mt-4 rounded-lg border border-green-500/30 bg-green-500/10 p-3">
                    <p className="text-sm text-green-400">
                      ✓ 일관성 비율(CR): {round2Data.consistency_ratio.toFixed(4)}
                    </p>
                    <p className="text-xs text-green-300 mt-1">
                      {round2Data.consistency_ratio <= 0.1
                        ? 'CR < 0.1로 일관성 기준을 충족합니다'
                        : 'CR이 0.1을 초과했지만 최선의 결과를 사용합니다'}
                    </p>
                  </div>
                </div>
              )}

            {/* Round 3: Decision Matrix */}
            {currentSubStep === 3 && round3Data && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#3b4354]">
                      <th className="pb-2 pr-2 text-left text-white">전공</th>
                      {Object.keys(Object.values(round3Data.decision_matrix)[0] || {}).map((criterion) => (
                        <th key={criterion} className="pb-2 px-1 text-right text-white">
                          {criterion.substring(0, 4)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(round3Data.decision_matrix).map(([major, scores]) => (
                      <tr key={major} className="border-b border-[#3b4354]/50">
                        <td className="py-2 pr-2 text-white truncate max-w-20">{major}</td>
                        {Object.values(scores).map((score, idx) => (
                          <td key={idx} className="py-2 px-1 text-right text-[#9ca6ba]">
                            {typeof score === 'number' ? score.toFixed(1) : score}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
