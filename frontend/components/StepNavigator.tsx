"use client";

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
                    className={`flex items-center justify-center size-8 rounded-full border-2 transition-colors ${step.id === currentStep
                      ? "border-[#FF1F55] bg-[#FF1F55] text-white"
                      : step.id < currentStep
                        ? "border-[#FF1F55] bg-transparent text-[#FF1F55]"
                        : "border-[#3b4354] bg-transparent text-[#9ca6ba]"
                      }`}
                  >
                    {step.id < currentStep ? (
                      <span className="material-symbols-outlined text-sm">check</span>
                    ) : (
                      <span className="text-sm">{step.id}</span>
                    )}
                  </div>
                  <span
                    className={`text-sm transition-colors hidden sm:inline ${step.id === currentStep
                      ? "text-white"
                      : step.id < currentStep
                        ? "text-[#FF1F55]"
                        : "text-[#9ca6ba]"
                      }`}
                  >
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`h-0.5 w-12 hidden sm:block ${step.id < currentStep ? "bg-[#FF1F55]" : "bg-[#3b4354]"
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
                className="gap-2 border-[#3b4354] bg-transparent text-white hover:bg-[#1b1f27] hover:text-white"
              >
                <span className="material-symbols-outlined mr-2 text-lg">arrow_back</span>
                <span className="hidden sm:inline">Previous</span>
              </Button>
            )}
            {currentStep < totalSteps && (
              <Button
                onClick={onNext}
                disabled={!canProceed}
                className="gap-2 bg-[#FF1F55] hover:bg-[#FF4572] text-white border-0"
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
          <div className="flex items-center justify-center mt-6">
            <div className="flex items-center gap-2">
              {subSteps.map((subStep, index) => (
                <div key={subStep.id} className="flex items-center gap-2">
                  <button
                    onClick={() => onSubStepChange?.(subStep.id)}
                    className={`flex items-center gap-2 group transition-all ${subStep.id === currentSubStep
                      ? "cursor-default"
                      : "cursor-pointer hover:scale-105"
                      }`}
                  >
                    <div
                      className={`size-2 rounded-full transition-all ${subStep.id === currentSubStep
                        ? "bg-[#FF1F55] scale-125"
                        : subStep.id < currentSubStep
                          ? "bg-[#FF1F55]/70"
                          : "bg-[#3b4354] group-hover:bg-[#9ca6ba]/50"
                        }`}
                    />
                    <span
                      className={`text-xs transition-colors ${subStep.id === currentSubStep
                        ? "text-white"
                        : subStep.id < currentSubStep
                          ? "text-[#FF1F55]/70"
                          : "text-[#9ca6ba] group-hover:text-white"
                        }`}
                    >
                      {subStep.label}
                    </span>
                  </button>
                  {index < subSteps.length - 1 && (
                    <div
                      className={`h-px w-8 ${subStep.id < currentSubStep ? "bg-[#FF1F55]/70" : "bg-[#3b4354]"
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