import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export interface DecisionMatrix {
  [major: string]: {
    [criterion: string]: number;
  };
}

interface DecisionMatrixTableProps {
  matrix: DecisionMatrix;
  criteria: string[];
}

export function DecisionMatrixTable({
  matrix,
  criteria,
}: DecisionMatrixTableProps) {
  const majors = Object.keys(matrix);

  // Helper to get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 8) return "bg-green-500/20 text-green-700 dark:text-green-400";
    if (score >= 6) return "bg-blue-500/20 text-blue-700 dark:text-blue-400";
    if (score >= 4) return "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400";
    return "bg-red-500/20 text-red-700 dark:text-red-400";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">의사결정 매트릭스</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="font-semibold">전공</TableHead>
                {criteria.map((criterion) => (
                  <TableHead key={criterion} className="text-center font-semibold">
                    {criterion}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {majors.map((major) => (
                <TableRow key={major}>
                  <TableCell className="font-medium">{major}</TableCell>
                  {criteria.map((criterion) => {
                    const score = matrix[major]?.[criterion] || 0;
                    return (
                      <TableCell
                        key={criterion}
                        className={`text-center ${getScoreColor(score)}`}
                      >
                        {score.toFixed(1)}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
