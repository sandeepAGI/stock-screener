import type { OutlierCategory } from '../../types';

interface ScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  const getColor = () => {
    if (score >= 70) return 'bg-green-100 text-green-800';
    if (score >= 50) return 'bg-yellow-100 text-yellow-800';
    if (score >= 30) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${getColor()} ${sizeClasses[size]}`}>
      {score.toFixed(1)}
    </span>
  );
}

interface OutlierBadgeProps {
  category: OutlierCategory;
  size?: 'sm' | 'md';
}

export function OutlierBadge({ category, size = 'md' }: OutlierBadgeProps) {
  const config: Record<OutlierCategory, { label: string; className: string }> = {
    strong_undervalued: {
      label: 'Strong Undervalued',
      className: 'bg-emerald-100 text-emerald-800',
    },
    undervalued: {
      label: 'Undervalued',
      className: 'bg-green-100 text-green-800',
    },
    fairly_valued: {
      label: 'Fairly Valued',
      className: 'bg-gray-100 text-gray-800',
    },
    overvalued: {
      label: 'Overvalued',
      className: 'bg-orange-100 text-orange-800',
    },
    strong_overvalued: {
      label: 'Strong Overvalued',
      className: 'bg-red-100 text-red-800',
    },
  };

  const { label, className } = config[category];

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${className} ${sizeClasses[size]}`}>
      {label}
    </span>
  );
}
