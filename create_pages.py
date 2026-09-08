import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

write_file("frontend_app/src/pages/Dashboard.tsx", """
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import clsx from 'clsx';
import { Activity, ShieldAlert, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metRes, txRes] = await Promise.all([
          api.get('/dashboard/metrics'),
          api.get('/transactions?limit=15')
        ]);
        setMetrics(metRes.data);
        setTransactions(txRes.data.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div className="p-8 text-center">Loading radar...</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Transactions" value={metrics.transactions_total} icon={<Activity />} />
        <MetricCard title="Approved" value={metrics.approved} icon={<CheckCircle className="text-success" />} />
        <MetricCard title="Under Review" value={metrics.review} icon={<AlertTriangle className="text-warning" />} />
        <MetricCard title="Held (Fraud)" value={metrics.held} icon={<AlertOctagon className="text-danger" />} />
      </div>

      <div className="bg-panel border border-border rounded-lg overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-border bg-panel/50 font-medium text-white flex justify-between items-center">
          <span>Live Risk Stream</span>
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
          </span>
        </div>
        <div className="divide-y divide-border">
          {transactions.map(tx => (
            <div 
              key={tx.id} 
              className="px-6 py-3 hover:bg-zinc-800/50 cursor-pointer flex items-center justify-between text-sm transition-colors"
              onClick={() => navigate(`/transactions/${tx.id}`)}
            >
              <div className="flex flex-col">
                <span className="font-mono text-zinc-300">{tx.id.split('-')[0]}</span>
                <span className="text-xs text-zinc-500">{new Date(tx.time * 1000).toLocaleTimeString()}</span>
              </div>
              <div className="font-medium text-white">₹{tx.amount.toFixed(2)}</div>
              <div className="flex items-center space-x-4 w-48 justify-end">
                {tx.risk_score !== undefined ? (
                  <>
                    <div className="flex flex-col items-end">
                      <span className="text-xs text-zinc-500">Risk Score</span>
                      <span className="font-mono">{tx.risk_score.toFixed(0)}</span>
                    </div>
                    <DecisionBadge decision={tx.decision} />
                  </>
                ) : (
                  <span className="text-zinc-500 text-xs">Evaluating...</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon }: any) {
  return (
    <div className="bg-panel border border-border rounded-lg p-5 flex items-center justify-between shadow-sm hover:border-primary/50 transition-colors">
      <div>
        <div className="text-zinc-400 text-sm font-medium mb-1">{title}</div>
        <div className="text-3xl font-bold text-white">{value.toLocaleString()}</div>
      </div>
      <div className="text-zinc-500 w-8 h-8">{icon}</div>
    </div>
  );
}

export function DecisionBadge({ decision }: { decision: str }) {
  return (
    <span className={clsx(
      "px-2.5 py-1 rounded text-xs font-bold w-20 text-center",
      decision === 'APPROVE' ? "bg-success/10 text-success" :
      decision === 'REVIEW' ? "bg-warning/10 text-warning" :
      "bg-danger/10 text-danger"
    )}>
      {decision}
    </span>
  );
}
""")

write_file("frontend_app/src/pages/FraudLab.tsx", """
import { useState } from 'react';
import api from '../services/api';
import { ShieldAlert, Play, Activity } from 'lucide-react';

export default function FraudLab() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const launchAttack = async (type: string, size: int) => {
    setLoading(true);
    setMessage('Launching...');
    try {
      const res = await api.post('/simulator/run', { attack_type: type, attack_size: size });
      setMessage(res.data.message);
    } catch (err: any) {
      setMessage('Error launching attack');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center py-10 space-y-4">
        <ShieldAlert className="w-16 h-16 text-danger mx-auto" />
        <h1 className="text-4xl font-bold text-white">FRAUD LAB</h1>
        <p className="text-zinc-400 text-lg">Simulate attacks against the Sentinel control tower.</p>
      </div>

      {message && (
        <div className="p-4 bg-primary/10 border border-primary/20 text-primary rounded-lg text-center font-medium animate-pulse">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <AttackCard 
          title="Account Takeover" 
          desc="Rapid login failures followed by a high-value transaction from an unknown device."
          type="ACCOUNT_TAKEOVER"
          size={1}
          onLaunch={launchAttack}
          loading={loading}
        />
        <AttackCard 
          title="Velocity Burst" 
          desc="Multiple rapid low-value transactions within seconds using the same card."
          type="VELOCITY_BURST"
          size={8}
          onLaunch={launchAttack}
          loading={loading}
        />
        <AttackCard 
          title="Coordinated Fraud Ring" 
          desc="Massive attack spanning multiple synchronized accounts sharing the same underlying IP/Device cluster."
          type="MULTIPLE_SIGNALS"
          size={5}
          onLaunch={launchAttack}
          loading={loading}
        />
      </div>
    </div>
  );
}

function AttackCard({ title, desc, type, size, onLaunch, loading }: any) {
  return (
    <div className="bg-panel border border-border rounded-lg p-6 flex flex-col justify-between hover:border-danger/50 transition-colors">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
        <p className="text-zinc-400 text-sm mb-6">{desc}</p>
      </div>
      <button 
        onClick={() => onLaunch(type, size)}
        disabled={loading}
        className="flex items-center justify-center w-full py-2.5 bg-danger/10 text-danger font-bold rounded hover:bg-danger/20 transition-colors disabled:opacity-50"
      >
        <Play className="w-4 h-4 mr-2" />
        LAUNCH ATTACK
      </button>
    </div>
  );
}
""")
print("Wrote pages")
