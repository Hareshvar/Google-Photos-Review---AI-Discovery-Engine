import React from 'react';

interface PipelineStepProps {
  stepNumber: number;
  title: string;
  countLabel: string;
  subtitle: string;
  icon: string;
  isHighlighted?: boolean;
  highlightVariant?: 'blue' | 'green';
}

export const PipelineStep: React.FC<PipelineStepProps> = ({
  stepNumber,
  title,
  countLabel,
  subtitle,
  icon,
  isHighlighted = false,
  highlightVariant = 'blue',
}) => {
  const isGreen = isHighlighted && highlightVariant === 'green';
  const isBlue = isHighlighted && highlightVariant === 'blue';

  return (
    <div
      className={`flex flex-col border rounded-xl p-4 transition-all ${
        isGreen
          ? 'bg-[#e6f4ea] border-[#ceead6] shadow-sm'
          : isBlue
          ? 'bg-[#e8f0fe] border-[#d2e3fc] shadow-sm'
          : 'bg-surface-bg border-border-subtle hover:border-[#1a73e8]'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span
          className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-sm ${
            isGreen
              ? 'bg-[#137333] text-white'
              : isBlue
              ? 'bg-[#1a73e8] text-white'
              : 'bg-[#e8f0fe] text-[#1a73e8]'
          }`}
        >
          {stepNumber}
        </span>
        <span
          className={`material-symbols-outlined text-[20px] ${
            isGreen
              ? 'text-[#137333]'
              : isBlue
              ? 'text-[#1a73e8]'
              : 'text-on-surface-variant'
          }`}
        >
          {icon}
        </span>
      </div>
      <span className="font-semibold text-on-surface text-base">{title}</span>
      <span
        className={`font-bold text-sm mt-1 ${
          isGreen ? 'text-[#137333]' : 'text-[#1a73e8]'
        }`}
      >
        {countLabel}
      </span>
      <span className="text-xs text-on-secondary-container mt-2 leading-snug">
        {subtitle}
      </span>
    </div>
  );
};
