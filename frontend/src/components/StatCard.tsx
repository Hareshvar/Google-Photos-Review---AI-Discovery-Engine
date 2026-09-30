import React from 'react';

interface StatCardProps {
  title: string;
  count: number;
  badge?: string;
  subtitle: string;
  color: 'blue' | 'green' | 'yellow' | 'red';
  icon: string;
}

const colorStyles = {
  blue: {
    bg: 'bg-[#e8f0fe]',
    border: 'border-[#d2e3fc]',
    text: 'text-[#1a73e8]',
    iconBg: 'bg-white',
    badgeBg: 'bg-white/80',
  },
  green: {
    bg: 'bg-[#e6f4ea]',
    border: 'border-[#ceead6]',
    text: 'text-[#137333]',
    iconBg: 'bg-white',
    badgeBg: 'bg-white/80',
  },
  yellow: {
    bg: 'bg-[#fef7e0]',
    border: 'border-[#feefc3]',
    text: 'text-[#b06000]',
    iconBg: 'bg-white',
    badgeBg: 'bg-white/80',
  },
  red: {
    bg: 'bg-[#fce8e6]',
    border: 'border-[#fad2cf]',
    text: 'text-[#c5221f]',
    iconBg: 'bg-white',
    badgeBg: 'bg-white/80',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  count,
  badge,
  subtitle,
  color,
  icon,
}) => {
  const styles = colorStyles[color];

  return (
    <div
      className={`relative overflow-hidden ${styles.bg} border ${styles.border} rounded-2xl p-5 flex flex-col justify-between shadow-sm transition-all hover:shadow-md`}
    >
      <div className="flex items-center justify-between">
        <span className={`text-sm font-semibold tracking-wide ${styles.text}`}>
          {title}
        </span>
        <div
          className={`w-9 h-9 rounded-full ${styles.iconBg} flex items-center justify-center ${styles.text} shadow-sm`}
        >
          <span className="material-symbols-outlined text-[20px]">{icon}</span>
        </div>
      </div>
      <div className="mt-5">
        <div className="flex items-baseline gap-2">
          <span className={`text-[32px] leading-9 font-bold tracking-tight ${styles.text}`}>
            {count.toLocaleString()}
          </span>
          {badge && (
            <span
              className={`text-sm font-bold px-2 py-0.5 rounded-full ${styles.badgeBg} ${styles.text}`}
            >
              {badge}
            </span>
          )}
        </div>
        <p className="text-sm text-[#3c4043] mt-2">{subtitle}</p>
      </div>
    </div>
  );
};
