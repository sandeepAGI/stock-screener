import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Database,
  TrendingUp,
  RotateCcw,
  Sliders,
  Loader2,
  RefreshCw,
  Brain,
  Calculator,
  CheckCircle,
} from 'lucide-react';
import { useWeightsContext } from '../../context/WeightsContext';
import { useOperationContext } from '../../context/OperationContext';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analysis', icon: Search, label: 'Stock Analysis' },
  { to: '/data', icon: Database, label: 'Data Management' },
];

interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  color: string;
}

function WeightSlider({ label, value, onChange, color }: SliderProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className={`font-medium ${color}`}>{value}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-thumb"
        style={{
          background: `linear-gradient(to right, ${color === 'text-blue-400' ? '#60a5fa' : color === 'text-purple-400' ? '#c084fc' : color === 'text-green-400' ? '#4ade80' : '#facc15'} 0%, ${color === 'text-blue-400' ? '#60a5fa' : color === 'text-purple-400' ? '#c084fc' : color === 'text-green-400' ? '#4ade80' : '#facc15'} ${value}%, #334155 ${value}%, #334155 100%)`,
        }}
      />
    </div>
  );
}

// Operation status indicator component
function OperationStatusIndicator() {
  const { operation } = useOperationContext();

  // Show indicator if active OR if recently completed (within 10 seconds)
  const showIndicator = operation.isActive ||
    (operation.completedAt && Date.now() - operation.completedAt < 10000);

  if (!showIndicator) return null;

  const getOperationIcon = () => {
    // Show checkmark when completed
    if (!operation.isActive && operation.completedAt) {
      return <CheckCircle className="w-4 h-4" />;
    }
    switch (operation.type) {
      case 'data':
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'sentiment':
        return <Brain className="w-4 h-4" />;
      case 'calculate':
        return <Calculator className="w-4 h-4" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin" />;
    }
  };

  const getOperationColor = () => {
    // Show green when completed successfully
    if (!operation.isActive && operation.completedAt && !operation.status.includes('Error')) {
      return 'bg-green-600';
    }
    // Show red for errors
    if (operation.status.includes('Error')) {
      return 'bg-red-600';
    }
    switch (operation.type) {
      case 'data':
        return 'bg-blue-600';
      case 'sentiment':
        return 'bg-purple-600';
      case 'calculate':
        return 'bg-green-600';
      default:
        return 'bg-slate-600';
    }
  };

  return (
    <div className={`mx-4 mb-2 p-3 rounded-lg ${getOperationColor()}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {getOperationIcon()}
          <span className="text-xs font-medium truncate">{operation.status}</span>
        </div>
        {operation.progress !== undefined && operation.progress > 0 && (
          <span className="text-xs font-bold whitespace-nowrap">
            {Math.round(operation.progress)}%
          </span>
        )}
      </div>
      {operation.progress !== undefined && operation.progress > 0 && (
        <div className="mt-2 w-full bg-white/20 rounded-full h-1.5">
          <div
            className="bg-white h-1.5 rounded-full transition-all"
            style={{ width: `${operation.progress}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  const { weights, normalizedWeights, setWeight, resetWeights, isDefault } = useWeightsContext();

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg">StockAnalyzer</h1>
            <p className="text-xs text-slate-400">Pro Edition</p>
          </div>
        </div>
      </div>

      {/* Global Operation Status */}
      <OperationStatusIndicator />

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Weight Adjustment */}
        <div className="mt-6 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between mb-3 px-1">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-slate-400" />
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Weight Adjustment
              </h3>
            </div>
            {!isDefault && (
              <button
                onClick={resetWeights}
                className="p-1 text-slate-400 hover:text-white transition-colors"
                title="Reset to default"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="space-y-3 px-1">
            <WeightSlider
              label="Fundamental"
              value={weights.fundamental}
              onChange={(v) => setWeight('fundamental', v)}
              color="text-blue-400"
            />
            <WeightSlider
              label="Quality"
              value={weights.quality}
              onChange={(v) => setWeight('quality', v)}
              color="text-purple-400"
            />
            <WeightSlider
              label="Growth"
              value={weights.growth}
              onChange={(v) => setWeight('growth', v)}
              color="text-green-400"
            />
            <WeightSlider
              label="Sentiment"
              value={weights.sentiment}
              onChange={(v) => setWeight('sentiment', v)}
              color="text-yellow-400"
            />
          </div>

          {/* Normalized weights display */}
          <div className="mt-3 px-1">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Normalized:</span>
              <span>
                {(normalizedWeights.fundamental * 100).toFixed(0)}/
                {(normalizedWeights.quality * 100).toFixed(0)}/
                {(normalizedWeights.growth * 100).toFixed(0)}/
                {(normalizedWeights.sentiment * 100).toFixed(0)}
              </span>
            </div>
          </div>
        </div>

      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700">
        <p className="text-xs text-slate-500 text-center">v1.0.0</p>
      </div>
    </aside>
  );
}
