import { Header } from "./Header";
import { StepNavigator } from "./StepNavigator";

interface PageLayoutProps {
  children: React.ReactNode;
  currentStep: number;
  showHeader?: boolean;
  showSteps?: boolean;
}

export function PageLayout({
  children,
  currentStep,
  showHeader = true,
  showSteps = true,
}: PageLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      {showHeader && <Header />}

      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">
          {showSteps && <StepNavigator currentStep={currentStep} />}
          {children}
        </div>
      </main>
    </div>
  );
}
