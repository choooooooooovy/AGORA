import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";

export interface CriteriaWeights {
  [key: string]: number;
}

interface CriteriaWeightsPanelProps {
  weights: CriteriaWeights;
}

export function CriteriaWeightsPanel({ weights }: CriteriaWeightsPanelProps) {
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
        {sortedWeights.map(([criterion, weight]) => (
          <div key={criterion} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{criterion}</span>
              <span className="text-muted-foreground">
                {(weight * 100).toFixed(1)}%
              </span>
            </div>
            <Progress value={weight * 100} className="h-2" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
