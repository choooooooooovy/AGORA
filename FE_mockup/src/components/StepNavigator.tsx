import { Button } from "./ui/button";

interface Step {
  id: number;
  label: string;
}

interface SubStep {
  id: number;
  label: string;
}

interface StepNavigatorProps {
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onPrevious: () => void;
  canProceed: boolean;
  steps: Step[];
  subSteps?: SubStep[];
  currentSubStep?: number;
  onSubStepChange?: (subStepId: number) => void;
}

export function StepNavigator({
  currentStep,
  totalSteps,
  onNext,
  onPrevious,
  canProceed,
  steps,
  subSteps,
  currentSubStep,
  onSubStepChange,
}: StepNavigatorProps) {
  const hasSubSteps = subSteps && subSteps.length > 0 && currentSubStep !== undefined;

  return (
    <div className="w-full border-b border-[#282e39] bg-[#0a0d12]/50 backdrop-blur-sm">
      <div className="px-6 sm:px-10 lg:px-20 py-6">
        <div className="flex items-center justify-center relative">
          {/* Step Indicators - Centered */}
          <div className="flex items-center gap-3">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex items-center justify-center size-8 rounded-full border-2 transition-colors ${
                      step.id === currentStep
                        ? "border-[#FF1F55] bg-[#FF1F55] text-white"
                        : step.id < currentStep
                        ? "border-[#FF1F55] bg-transparent text-[#FF1F55]"
                        : "border-[#3b4354] bg-transparent text-[#6b7280]"
                    }`}
                  >
                    {step.id < currentStep ? (
                      <span className="material-symbols-outlined text-sm">check</span>
                    ) : (
                      <span className="text-sm">{step.id}</span>
                    )}
                  </div>
                  <span
                    className={`hidden sm:inline transition-colors ${
                      step.id === currentStep
                        ? "text-white"
                        : step.id < currentStep
                        ? "text-[#FF1F55]"
                        : "text-[#6b7280]"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`hidden sm:block w-12 h-0.5 ${
                      step.id < currentStep ? "bg-[#FF1F55]" : "bg-[#3b4354]"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          {/* Navigation Buttons - Absolute positioned on the right */}
          <div className="absolute right-0 flex items-center gap-3">
            {currentStep > 1 && (
              <Button
                onClick={onPrevious}
                variant="outline"
                className="border-[#3b4354] bg-transparent text-white hover:bg-[#1b1f27] hover:border-[#FF1F55]"
              >
                <span className="material-symbols-outlined mr-2 text-lg">arrow_back</span>
                <span className="hidden sm:inline">Previous</span>
              </Button>
            )}
            {currentStep < totalSteps && (
              <Button
                onClick={onNext}
                disabled={!canProceed}
                className="bg-[#FF1F55] hover:bg-[#FF4572] text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="hidden sm:inline">Next Step</span>
                <span className="sm:hidden">Next</span>
                <span className="material-symbols-outlined ml-2 text-lg">arrow_forward</span>
              </Button>
            )}
          </div>
        </div>

        {/* Sub Steps */}
        {hasSubSteps && (
          <div className="mt-6 flex items-center justify-center">
            <div className="flex items-center gap-2">
              {subSteps.map((subStep, index) => (
                <div key={subStep.id} className="flex items-center gap-2">
                  <button
                    onClick={() => onSubStepChange?.(subStep.id)}
                    className={`group flex items-center gap-2 transition-all ${
                      subStep.id === currentSubStep ? "cursor-default" : "cursor-pointer hover:scale-105"
                    }`}
                  >
                    <div
                      className={`size-2 rounded-full transition-all ${
                        subStep.id === currentSubStep
                          ? "bg-[#FF1F55] scale-125"
                          : subStep.id < currentSubStep
                          ? "bg-[#FF4572]"
                          : "bg-[#3b4354] group-hover:bg-[#4b5364]"
                      }`}
                    />
                    <span
                      className={`text-xs transition-colors ${
                        subStep.id === currentSubStep
                          ? "text-white"
                          : subStep.id < currentSubStep
                          ? "text-[#FF4572]"
                          : "text-[#6b7280] group-hover:text-[#8b9280]"
                      }`}
                    >
                      {subStep.label}
                    </span>
                  </button>
                  {index < subSteps.length - 1 && (
                    <div
                      className={`w-8 h-px ${
                        subStep.id < currentSubStep ? "bg-[#FF4572]" : "bg-[#3b4354]"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}