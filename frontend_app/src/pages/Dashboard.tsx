import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import clsx from 'clsx';
import { Activity, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

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

export function DecisionBadge({ decision }: { decision: string }) {
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
