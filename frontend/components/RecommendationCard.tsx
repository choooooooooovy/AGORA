import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";

export interface Recommendation {
  rank: number;
  major: string;
  topsisScore: number;
  strengths: string[];
  weaknesses: string[];
  progressPercentage: number;
}

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const rankColors = {
  1: "bg-gradient-to-br from-yellow-400 to-yellow-600",
  2: "bg-gradient-to-br from-gray-300 to-gray-500",
  3: "bg-gradient-to-br from-orange-400 to-orange-600",
};

const rankEmojis = {
  1: "🥇",
  2: "🥈",
  3: "🥉",
};

export function RecommendationCard({
  recommendation,
}: RecommendationCardProps) {
  const { rank, major, topsisScore, strengths, weaknesses, progressPercentage } =
    recommendation;

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className={`${rankColors[rank as keyof typeof rankColors]} text-white`}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-xl">
            <span className="text-2xl">{rankEmojis[rank as keyof typeof rankEmojis]}</span>
            {major}
          </CardTitle>
          <Badge variant="secondary" className="bg-white/20 text-white">
            #{rank}
          </Badge>
        </div>
        <p className="text-sm opacity-90">
          TOPSIS 점수: {(topsisScore * 100).toFixed(2)}점
        </p>
      </CardHeader>
      <CardContent className="space-y-4 pt-6">
        {/* Strengths */}
        <div>
          <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
            <span>✅</span> 강점
          </h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {strengths.map((strength, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="mt-1 text-xs">•</span>
                <span>{strength}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        {weaknesses.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <span>⚠️</span> 개선 필요
            </h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {weaknesses.map((weakness, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="mt-1 text-xs">•</span>
                  <span>{weakness}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">적합도</span>
            <span className="font-medium">{progressPercentage.toFixed(1)}%</span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
