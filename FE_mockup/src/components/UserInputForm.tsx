import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { X } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";

interface UserInputFormProps {
  interests: string;
  aptitudes: string;
  pursuitValues: string;
  candidateMajors: string[];
  onInterestsChange: (value: string) => void;
  onAptitudesChange: (value: string) => void;
  onPursuitValuesChange: (value: string) => void;
  onCandidateMajorsChange: (majors: string[]) => void;
  onGenerateAgents: () => void;
  isGenerating: boolean;
}

export function UserInputForm({
  interests,
  aptitudes,
  pursuitValues,
  candidateMajors,
  onInterestsChange,
  onAptitudesChange,
  onPursuitValuesChange,
  onCandidateMajorsChange,
  onGenerateAgents,
  isGenerating,
}: UserInputFormProps) {
  // 단과대학별 전공 목록
  const majorsByCollege = {
    공학대학: [
      "건축학전공",
      "건축공학전공",
      "건설환경공학과",
      "교통·물류공학과",
      "전자공학부",
      "배터리소재화학공학과",
      "기계공학과",
      "산업경영공학과",
      "로봇공학과",
      "에너지바이오학과",
      "해양융합공학과",
    ],
    소프트웨어융합대학: [
      "컴퓨터학부 컴퓨터전공",
      "컴퓨터학부 지능형클라우드전공",
      "ICT융합학부 데이터인텔리전스전공",
      "ICT융합학부 디자인컨버전스전공",
      "인공지능학과",
      "수리데이터사이언스학과",
    ],
    첨단융합대학: [
      "차세대반도체융합공학부 신소재·반도체공학전공",
      "차세대반도체융합공학부 반도체·디스플레이공학전공",
      "바이오신약융합학부 분자의약전공",
      "바이오신약융합학부 바이오나노공학전공",
      "국방지능정보융합공학부 지능정보양자공학전공",
    ],
    글로벌문화통상대학: ["글로벌문화통상학부"],
    "커뮤니케이션&컬처대학": [
      "광고홍보학과",
      "미디어학과",
      "문화인류학과",
      "문화콘텐츠학과",
    ],
    경상대학: ["경영학부", "경제학부", "보험계리학과"],
    디자인대학: [
      "주얼리·패션디자인학과",
      "융합디자인학부",
      "영상디자인학과",
    ],
  };

  const isFormValid =
    interests.trim() &&
    aptitudes.trim() &&
    pursuitValues.trim() &&
    candidateMajors.length >= 3;

  const toggleMajor = (major: string) => {
    if (candidateMajors.includes(major)) {
      onCandidateMajorsChange(
        candidateMajors.filter((m) => m !== major),
      );
    } else {
      onCandidateMajorsChange([...candidateMajors, major]);
    }
  };

  const removeMajor = (major: string) => {
    onCandidateMajorsChange(
      candidateMajors.filter((m) => m !== major),
    );
  };

  return (
    <div className="flex flex-col gap-6 flex-1 overflow-y-auto">
      {/* Interests */}
      <label className="flex flex-col">
        <p className="text-white pb-3">흥미</p>
        <Textarea
          value={interests}
          onChange={(e) => onInterestsChange(e.target.value)}
          placeholder="예: 복잡한 수학 문제를 푸는 과정이 즐겁고, 프로그래밍으로 알고리즘을 구현하는 것에 흥미가 있습니다."
          disabled={isGenerating}
          className="resize-none h-24 border-[#3b4354] bg-[#1b1f27] text-white placeholder:text-[#9ca6ba] focus:ring-2 focus:ring-[#FF1F55]/50 focus:border-[#FF1F55]"
        />
      </label>

      {/* Aptitudes */}
      <label className="flex flex-col">
        <p className="text-white pb-3">적성</p>
        <Textarea
          value={aptitudes}
          onChange={(e) => onAptitudesChange(e.target.value)}
          placeholder="예: 논리적 사고력이 뛰어나고 코딩 능력이 우수합니다. 수학 경시대회에서 입상한 경험이 있습니다."
          disabled={isGenerating}
          className="resize-none h-24 border-[#3b4354] bg-[#1b1f27] text-white placeholder:text-[#9ca6ba] focus:ring-2 focus:ring-[#FF1F55]/50 focus:border-[#FF1F55]"
        />
      </label>

      {/* Pursuit Values */}
      <label className="flex flex-col">
        <p className="text-white pb-3">추구 가치</p>
        <Textarea
          value={pursuitValues}
          onChange={(e) =>
            onPursuitValuesChange(e.target.value)
          }
          placeholder="예: 높은 연봉과 빠른 커리어 성장을 원하며, 워라밸도 중요하게 생각합니다."
          disabled={isGenerating}
          className="resize-none h-24 border-[#3b4354] bg-[#1b1f27] text-white placeholder:text-[#9ca6ba] focus:ring-2 focus:ring-[#FF1F55]/50 focus:border-[#FF1F55]"
        />
      </label>

      {/* Candidate Majors */}
      <div className="flex flex-col gap-3">
        <div className="flex items-baseline justify-between">
          <p className="text-white">
            비교할 전공 선택 (최소 3개)
          </p>
          <p className="text-[#9ca6ba] text-sm">
            선택됨: {candidateMajors.length}개
          </p>
        </div>

        {/* Selected Majors - Tags */}
        {candidateMajors.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 bg-black/20 border border-[#282e39] rounded-lg">
            {candidateMajors.map((major) => (
              <Badge
                key={major}
                className="bg-[#FF1F55] hover:bg-[#FF4572] text-white px-3 py-1 flex items-center gap-2"
              >
                <span>{major}</span>
                <button
                  onClick={() => removeMajor(major)}
                  disabled={isGenerating}
                  className="hover:bg-white/20 rounded-full p-0.5"
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}

        {/* Majors by College - Accordion */}
        <Accordion type="multiple" className="w-full">
          {Object.entries(majorsByCollege).map(([college, majors]) => (
            <AccordionItem key={college} value={college} className="border-[#3b4354]">
              <AccordionTrigger className="text-white hover:text-[#FF1F55] hover:no-underline">
                {college} ({majors.length})
              </AccordionTrigger>
              <AccordionContent>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  {majors.map((major) => (
                    <button
                      key={major}
                      onClick={() => toggleMajor(major)}
                      disabled={isGenerating}
                      className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                        candidateMajors.includes(major)
                          ? "bg-[#FF1F55] border-[#FF1F55] text-white"
                          : "bg-[#1b1f27] border-[#3b4354] text-[#9ca6ba] hover:border-[#FF1F55]/50"
                      }`}
                    >
                      {major}
                    </button>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <Button
        onClick={onGenerateAgents}
        disabled={!isFormValid || isGenerating}
        className="w-full h-16 bg-[#FF1F55] hover:bg-[#FF4572] text-white"
      >
        <span className="material-symbols-outlined mr-2">
          auto_awesome
        </span>
        <span>
          {isGenerating
            ? "에이전트 생성 중..."
            : "에이전트 생성"}
        </span>
      </Button>
    </div>
  );
}