"use client";

import { UIAgent, DecisionMatrix } from "@/lib/types";
import { Award, Sparkles, Target } from "lucide-react";

interface MajorRecommendation {
  major: string;
  rank: number;
  closeness_coefficient: number;
}

interface ReviewExportProps {
  recommendations: MajorRecommendation[];
  candidateMajors: string[];
  agents: UIAgent[];
  criteriaWeights?: Record<string, number>;
  decisionMatrix?: DecisionMatrix;
}

export function ReviewExport({
  recommendations,
  candidateMajors,
  criteriaWeights: propCriteriaWeights,
  decisionMatrix: propDecisionMatrix
}: ReviewExportProps) {
  // Sort majors by TOPSIS rank
  const sortedMajors = recommendations.length > 0
    ? recommendations.sort((a, b) => a.rank - b.rank).map(r => r.major)
    : candidateMajors.length > 0
      ? candidateMajors
      : ["컴퓨터공학", "데이터사이언스", "철학"];

  // Get icon for criterion based on keywords
  const getCriterionIcon = (criterionName: string): string => {
    const name = criterionName.toLowerCase();

    // 경제/커리어
    if (name.includes('경제') || name.includes('연봉') || name.includes('수익')) return '💰';
    if (name.includes('취업') || name.includes('고용')) return '💼';
    if (name.includes('안정')) return '🏦';

    // 적성/능력
    if (name.includes('적성')) return '🎯';
    if (name.includes('논리') || name.includes('추론')) return '🧠';
    if (name.includes('창의') || name.includes('혁신적')) return '✨';
    if (name.includes('문제') && name.includes('해결')) return '🔧';
    if (name.includes('분석')) return '📊';
    if (name.includes('데이터')) return '📈';
    if (name.includes('기술')) return '⚙️';

    // 창의성/예술
    if (name.includes('미적') || name.includes('심미')) return '🎨';
    if (name.includes('예술')) return '🖼️';
    if (name.includes('디자인')) return '✏️';

    // 사회성/협업
    if (name.includes('협동') || name.includes('협업')) return '🤝';
    if (name.includes('리더')) return '👥';
    if (name.includes('소통') || name.includes('커뮤니케이션')) return '💬';
    if (name.includes('팀')) return '🎭';

    // 가치관/영향력
    if (name.includes('사회') && name.includes('영향')) return '🌏';
    if (name.includes('윤리')) return '⚖️';
    if (name.includes('기여')) return '🌱';

    // 라이프스타일
    if (name.includes('워라밸') || name.includes('균형')) return '🏖️';
    if (name.includes('유연')) return '🕐';

    // 혁신/미래
    if (name.includes('혁신')) return '💡';
    if (name.includes('미래') || name.includes('잠재')) return '🚀';
    if (name.includes('성장')) return '📶';
    if (name.includes('변화') || name.includes('적응')) return '🔄';

    // 기본값
    return '📊';
  };

  // Transform propCriteriaWeights to array format with icons
  const criteriaWeights = propCriteriaWeights
    ? Object.entries(propCriteriaWeights).map(([name, weight]) => ({
      name,
      weight: weight * 100, // Convert to percentage
      icon: getCriterionIcon(name),
    }))
    : [];

  const getMajorInsights = (major: string) => {
    if (!propDecisionMatrix || !propDecisionMatrix[major]) {
      return { strengths: [], weaknesses: [] };
    }

    const scores = propDecisionMatrix[major];
    const allScores = Object.entries(scores).map(([name, score]) => ({
      name,
      score,
    }));

    const sorted = [...allScores].sort((a, b) => b.score - a.score);
    return {
      strengths: sorted.slice(0, 2),
      weaknesses: sorted.slice(-2).reverse(),
    };
  };

  return (
    <div className="flex gap-6 h-full overflow-hidden">
      {/* Left Side - Rankings & Details */}
      <div className="flex-1 flex flex-col gap-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-white text-3xl font-bold">최종 전공 추천</h1>
            <p className="text-[#9ca6ba] mt-2">
              TOPSIS 분석을 통해 도출된 {sortedMajors.length}개 전공의 최종 순위
            </p>
          </div>
        </div>

        {/* Major Cards */}
        <div className="grid grid-cols-1 gap-4">
          {sortedMajors.map((major) => {
            const insights = getMajorInsights(major);
            // Get real TOPSIS rank and score from recommendations
            const recommendation = recommendations.find(r => r.major === major);
            const rank = recommendation?.rank ?? 0;
            const topsisScore = recommendation?.closeness_coefficient ?? 0;

            return (
              <div
                key={major}
                className={`bg-black/20 border rounded-xl p-6 ${rank === 1
                  ? "border-[#FF1F55] shadow-lg shadow-[#FF1F55]/10"
                  : "border-[#282e39]"
                  }`}
              >
                <div className="flex items-start gap-4">
                  {/* Rank Badge */}
                  <div
                    className={`flex items-center justify-center size-16 rounded-full shrink-0 ${rank === 1
                      ? "bg-linear-to-br from-yellow-400 to-yellow-600"
                      : rank === 2
                        ? "bg-linear-to-br from-gray-300 to-gray-500"
                        : rank === 3
                          ? "bg-linear-to-br from-orange-400 to-orange-600"
                          : "bg-linear-to-br from-gray-500 to-gray-700"
                      }`}
                  >
                    <span className="text-white text-xl font-bold">#{rank}</span>
                  </div>

                  <div className="flex-1">
                    {/* Major Name & Score */}
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-white text-xl font-semibold">{major}</h3>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-[#9ca6ba] text-sm">TOPSIS 점수:</span>
                          <span className="text-[#FF1F55] font-semibold">{topsisScore.toFixed(4)}</span>
                        </div>
                      </div>
                      {rank === 1 && (
                        <Award className="size-6 text-yellow-400" />
                      )}
                    </div>

                    {/* Strengths & Weaknesses */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-[#1b1f27] border border-[#282e39] rounded-lg p-3">
                        <h4 className="text-green-400 text-sm mb-2 flex items-center gap-2">
                          <Sparkles className="size-4" />
                          강점
                        </h4>
                        <ul className="space-y-1">
                          {insights.strengths.map((s, i) => (
                            <li key={i} className="text-[#d1d5db] text-sm flex items-center gap-2">
                              <span className="size-1.5 rounded-full bg-green-400" />
                              {s.name} ({s.score}/10)
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-[#1b1f27] border border-[#282e39] rounded-lg p-3">
                        <h4 className="text-orange-400 text-sm mb-2 flex items-center gap-2">
                          <Target className="size-4" />
                          개선 영역
                        </h4>
                        <ul className="space-y-1">
                          {insights.weaknesses.map((w, i) => (
                            <li key={i} className="text-[#d1d5db] text-sm flex items-center gap-2">
                              <span className="size-1.5 rounded-full bg-orange-400" />
                              {w.name} ({w.score}/10)
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Score Bar */}
                    <div className="w-full">
                      <div className="w-full bg-[#1b1f27] rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-linear-to-r from-[#FF1F55] to-[#FF4572] h-full transition-all duration-500"
                          style={{ width: `${topsisScore * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Side - Analysis Details */}
      <div className="w-96 shrink-0 flex flex-col gap-4 overflow-y-auto">
        {/* Criteria Weights */}
        <div className="bg-black/20 border border-[#282e39] rounded-lg p-4">
          <h3 className="text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[#FF1F55]">bar_chart</span>
            기준별 가중치
          </h3>
          <div className="space-y-3">
            {criteriaWeights.map((item, index) => (
              <div key={index} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm flex items-center gap-2">
                    <span>{item.icon}</span>
                    {item.name}
                  </span>
                  <span className="text-[#FF1F55] font-semibold">{item.weight.toFixed(1)}%</span>
                </div>
                <div className="h-1.5 bg-[#1b1f27] rounded-full overflow-hidden">
                  <div
                    className="bg-linear-to-r from-[#FF1F55] to-[#FF4572] h-full transition-all duration-500"
                    style={{ width: `${item.weight * 2}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Decision Matrix */}
        <div className="bg-black/20 border border-[#282e39] rounded-lg p-4">
          <h3 className="text-white mb-4">의사결정 매트릭스</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#282e39]">
                  <th className="text-left text-[#9ca6ba] pb-2 pr-2 whitespace-normal">전공</th>
                  {propDecisionMatrix && Object.keys(Object.values(propDecisionMatrix)[0] || {}).map((criterion) => (
                    <th key={criterion} className="text-center text-[#9ca6ba] px-1 pb-2 whitespace-normal leading-tight">
                      {criterion}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {propDecisionMatrix && sortedMajors.map((major, index) => {
                  const scores = propDecisionMatrix[major];
                  if (!scores) return null;
                  return (
                    <tr key={index} className="border-b border-[#282e39]/50">
                      <td className="text-white py-2 pr-2 whitespace-normal leading-tight">{major}</td>
                      {Object.values(scores).map((score, i) => (
                        <td key={i} className="text-center text-[#d1d5db] py-2">{score}</td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
