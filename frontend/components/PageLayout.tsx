import { Header } from "./Header";
import { StepNavigator } from "./StepNavigator";

interface Step {
  id: number;
  label: string;
}

interface SubStep {
  id: number;
  label: string;
}

interface PageLayoutProps {
  children: React.ReactNode;
  currentStep: number;
  showHeader?: boolean;
  showSteps?: boolean;
  totalSteps?: number;
  onNext?: () => void;
  onPrevious?: () => void;
  canProceed?: boolean;
  steps?: Step[];
  subSteps?: SubStep[];
  currentSubStep?: number;
  onSubStepChange?: (subStepId: number) => void;
}

export function PageLayout({
  children,
  currentStep,
  showHeader = true,
  showSteps = true,
  totalSteps = 3,
  onNext = () => { },
  onPrevious = () => { },
  canProceed = false,
  steps = [],
  subSteps,
  currentSubStep,
  onSubStepChange,
}: PageLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      {showHeader && <Header />}

      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">
          {showSteps && steps.length > 0 && (
            <StepNavigator
              currentStep={currentStep}
              totalSteps={totalSteps}
              onNext={onNext}
              onPrevious={onPrevious}
              canProceed={canProceed}
              steps={steps}
              subSteps={subSteps}
              currentSubStep={currentSubStep}
              onSubStepChange={onSubStepChange}
            />
          )}
          {children}
        </div>
      </main>
    </div>
  );
}
