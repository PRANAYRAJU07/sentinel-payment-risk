import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# --- App.tsx ---
write_file("frontend_app/src/App.tsx", """
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import TransactionDetail from './pages/TransactionDetail';
import FraudNetwork from './pages/FraudNetwork';
import FraudLab from './pages/FraudLab';
import AuditLog from './pages/AuditLog';
import Models from './pages/Models';
import Settings from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="transactions/:id" element={<TransactionDetail />} />
          <Route path="fraud-network" element={<FraudNetwork />} />
          <Route path="fraud-lab" element={<FraudLab />} />
          <Route path="models" element={<Models />} />
          <Route path="audit-log" element={<AuditLog />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
""")

# --- Layout ---
write_file("frontend_app/src/components/Layout.tsx", """
import { Outlet, NavLink } from 'react-router-dom';
import { Activity, ShieldAlert, Network, FlaskConical, FileText, Settings as SettingsIcon, BrainCircuit } from 'lucide-react';
import clsx from 'clsx';

export default function Layout() {
  const navItems = [
    { to: "/dashboard", icon: Activity, label: "Overview" },
    { to: "/transactions", icon: FileText, label: "Transactions" },
    { to: "/fraud-network", icon: Network, label: "Fraud Network" },
    { to: "/fraud-lab", icon: FlaskConical, label: "Fraud Lab" },
    { to: "/models", icon: BrainCircuit, label: "Models" },
    { to: "/audit-log", icon: ShieldAlert, label: "Audit Log" },
    { to: "/settings", icon: SettingsIcon, label: "Settings" }
  ];

  return (
    <div className="flex h-screen bg-background text-zinc-300 font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-panel border-r border-border flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <ShieldAlert className="text-primary w-6 h-6 mr-3" />
          <h1 className="text-xl font-bold tracking-tight text-white">SENTINEL</h1>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => clsx(
                "flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                isActive ? "bg-primary/10 text-primary" : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              )}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-border text-xs text-zinc-500">
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-success mr-2" />
            System Operational
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-panel border-b border-border flex items-center justify-between px-6 shrink-0">
          <div className="text-sm text-zinc-400 font-medium">Payment Risk Control Tower</div>
          <div className="flex items-center space-x-4">
            <div className="px-2 py-1 rounded bg-warning/20 text-warning text-xs font-bold tracking-wider">DEMO ENV</div>
            <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-bold text-white">A</div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
""")

# --- API Service ---
write_file("frontend_app/src/services/api.ts", """
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

export default api;
""")

print("Wrote frontend shell")
