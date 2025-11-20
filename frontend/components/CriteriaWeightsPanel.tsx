import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";

export interface CriteriaWeights {
  [key: string]: number;
}

interface CriteriaWeightsPanelProps {
  weights: CriteriaWeights;
}

export function CriteriaWeightsPanel({ weights }: CriteriaWeightsPanelProps) {
  // 기준별 고정 색상 배열
  const criteriaColors = [
    '#EF4444', // red-500
    '#EC4899', // pink-500  
    '#A855F7', // purple-500
    '#3B82F6', // blue-500
    '#10B981', // green-500
  ];

  // Sort by weight descending
  const sortedWeights = Object.entries(weights).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">기준별 가중치</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {sortedWeights.map(([criterion, weight], index) => (
          <div key={criterion} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{criterion}</span>
              <span className="text-muted-foreground">
                {(weight * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full transition-all duration-300 rounded-full"
                style={{
                  width: `${weight * 100}%`,
                  backgroundColor: criteriaColors[index % criteriaColors.length],
                }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
