import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  Search,
  Database,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/rankings', icon: BarChart3, label: 'Rankings' },
  { to: '/analysis', icon: Search, label: 'Stock Analysis' },
  { to: '/data', icon: Database, label: 'Data Management' },
];

export function Sidebar() {
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

      {/* Navigation */}
      <nav className="flex-1 p-4">
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

        {/* Outlier shortcuts */}
        <div className="mt-8">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-3">
            Quick Filters
          </h3>
          <ul className="space-y-1">
            <li>
              <NavLink
                to="/rankings?category=strong_undervalued"
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <TrendingDown className="w-4 h-4 text-emerald-400" />
                <span className="text-sm">Strong Undervalued</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/rankings?category=strong_overvalued"
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <TrendingUp className="w-4 h-4 text-red-400" />
                <span className="text-sm">Strong Overvalued</span>
              </NavLink>
            </li>
          </ul>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700">
        <p className="text-xs text-slate-500 text-center">v1.0.0</p>
      </div>
    </aside>
  );
}
