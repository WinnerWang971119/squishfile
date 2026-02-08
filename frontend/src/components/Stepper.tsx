interface Step {
  label: string;
  icon: string;
}

const STEPS: Step[] = [
  { label: "Upload", icon: "01" },
  { label: "Compress", icon: "02" },
  { label: "Download", icon: "03" },
];

interface StepperProps {
  currentStep: number;
  completedSteps: number[];
  onStepClick: (step: number) => void;
}

export function Stepper({ currentStep, completedSteps, onStepClick }: StepperProps) {
  return (
    <nav className="flex items-center justify-center gap-0 animate-fade-in">
      {STEPS.map((step, index) => {
        const stepNum = index + 1;
        const isCurrent = currentStep === stepNum;
        const isCompleted = completedSteps.includes(stepNum);
        const isClickable = isCompleted || isCurrent;
        const isLast = index === STEPS.length - 1;

        return (
          <div key={step.label} className="flex items-center">
            <button
              onClick={() => isClickable && onStepClick(stepNum)}
              disabled={!isClickable}
              className={`
                group flex items-center gap-3 px-5 py-2.5 rounded-full
                transition-all duration-300 ease-out
                font-[family-name:var(--font-display)] text-sm tracking-wide
                ${isCurrent
                  ? "bg-[#FFD60A]/10 text-[#FFD60A] shadow-[0_0_20px_rgba(255,214,10,0.08)]"
                  : isCompleted
                    ? "text-[#A1A1AA] hover:text-[#F5F5F4] hover:bg-[#1C1C1F] cursor-pointer"
                    : "text-[#3F3F46] cursor-default"
                }
              `}
            >
              <span
                className={`
                  inline-flex items-center justify-center
                  w-7 h-7 rounded-full text-xs font-bold
                  transition-all duration-300
                  ${isCurrent
                    ? "bg-[#FFD60A] text-[#0A0A0B]"
                    : isCompleted
                      ? "bg-[#27272A] text-[#34D399] group-hover:bg-[#34D399]/20"
                      : "bg-[#1C1C1F] text-[#3F3F46]"
                  }
                `}
              >
                {isCompleted && !isCurrent ? "\u2713" : step.icon}
              </span>
              <span className="hidden sm:inline">{step.label}</span>
            </button>

            {!isLast && (
              <div className="w-12 lg:w-20 h-px mx-1 relative overflow-hidden">
                <div className="absolute inset-0 bg-[#27272A]" />
                <div
                  className={`
                    absolute inset-y-0 left-0 bg-[#FFD60A]/40
                    transition-all duration-500 ease-out
                    ${isCompleted ? "w-full" : "w-0"}
                  `}
                />
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
