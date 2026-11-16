import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Eye, AlertCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getBadgeConfig = () => {
    switch (status) {
      case 'Passed':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-600 mr-1.5" />,
          label: 'Passed'
        };
      case 'Passed with Warnings':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          icon: <AlertTriangle className="w-4 h-4 text-amber-600 mr-1.5" />,
          label: 'Passed with Warnings'
        };
      case 'Needs Correction':
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          icon: <XCircle className="w-4 h-4 text-rose-600 mr-1.5" />,
          label: 'Needs Correction'
        };
      case 'Manual Review Required':
        return {
          bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
          icon: <Eye className="w-4 h-4 text-indigo-600 mr-1.5" />,
          label: 'Manual Review'
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          icon: <AlertCircle className="w-4 h-4 text-slate-600 mr-1.5" />,
          label: status || 'Pending'
        };
    }
  };

  const config = getBadgeConfig();
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : (size === 'lg' ? 'px-3.5 py-1.5 text-sm font-semibold' : 'px-2.5 py-1 text-xs font-medium');

  return (
    <span className={`inline-flex items-center rounded-full border ${config.bg} ${sizeClasses}`}>
      {config.icon}
      {config.label}
    </span>
  );
};
