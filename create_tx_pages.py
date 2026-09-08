import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

write_file("frontend_app/src/pages/Transactions.tsx", """
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { DecisionBadge } from './Dashboard';

export default function Transactions() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<any[]>([]);

  useEffect(() => {
    api.get('/transactions?limit=100').then(res => setTransactions(res.data.data));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white">Transactions</h2>
      <div className="bg-panel border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-800/50 text-zinc-400">
            <tr>
              <th className="px-6 py-3 font-medium">Transaction ID</th>
              <th className="px-6 py-3 font-medium">Time</th>
              <th className="px-6 py-3 font-medium">Amount</th>
              <th className="px-6 py-3 font-medium">Customer</th>
              <th className="px-6 py-3 font-medium">Risk Score</th>
              <th className="px-6 py-3 font-medium text-right">Decision</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {transactions.map(tx => (
              <tr 
                key={tx.id} 
                className="hover:bg-zinc-800/30 cursor-pointer transition-colors"
                onClick={() => navigate(`/transactions/${tx.id}`)}
              >
                <td className="px-6 py-3 font-mono text-zinc-300">{tx.id.split('-')[0]}</td>
                <td className="px-6 py-3 text-zinc-500">{new Date(tx.time * 1000).toLocaleString()}</td>
                <td className="px-6 py-3 text-white">₹{tx.amount.toFixed(2)}</td>
                <td className="px-6 py-3 font-mono text-xs text-zinc-400">{tx.customer_id}</td>
                <td className="px-6 py-3 font-mono">{tx.risk_score?.toFixed(0) || '-'}</td>
                <td className="px-6 py-3 flex justify-end">
                  <DecisionBadge decision={tx.decision || 'PENDING'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
""")

write_file("frontend_app/src/pages/TransactionDetail.tsx", """
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import { DecisionBadge } from './Dashboard';
import { Bot, ShieldAlert, Check, X } from 'lucide-react';

export default function TransactionDetail() {
  const { id } = useParams();
  const [tx, setTx] = useState<any>(null);
  const [investigating, setInvestigating] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  const fetchTx = () => {
    api.get(`/transactions/${id}`).then(res => setTx(res.data)).catch(console.error);
  };

  useEffect(() => { fetchTx(); }, [id]);

  const runInvestigation = async () => {
    setInvestigating(true);
    await api.post(`/investigations/${id}/run`);
    fetchTx();
    setInvestigating(false);
  };
  
  const submitReview = async (action: string) => {
    setReviewing(true);
    await api.post(`/analyst-review`, { transaction_id: id, action, reason: 'Analyst Override via Dashboard' });
    fetchTx();
    setReviewing(false);
  };

  if (!tx) return <div className="p-8">Loading...</div>;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Transaction {tx.id.split('-')[0]}</h2>
          <p className="text-zinc-500 text-sm">{new Date(tx.time * 1000).toLocaleString()}</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-zinc-400 text-sm">Risk Score</div>
            <div className="text-3xl font-bold font-mono text-white">{tx.risk_score?.score?.toFixed(0) || '-'}</div>
          </div>
          <DecisionBadge decision={tx.risk_score?.decision || 'PENDING'} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-panel border border-border rounded-lg p-5 space-y-4">
          <h3 className="font-bold text-white border-b border-border pb-2">Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-zinc-500">Amount</span><span className="font-medium text-white">₹{tx.amount}</span></div>
            <div className="flex justify-between"><span className="text-zinc-500">Customer</span><span className="font-mono text-xs">{tx.customer_id}</span></div>
            <div className="flex justify-between"><span className="text-zinc-500">Device</span><span className="font-mono text-xs">{tx.device_id}</span></div>
            <div className="flex justify-between"><span className="text-zinc-500">IP Address</span><span className="font-mono text-xs">{tx.ip_address}</span></div>
          </div>
        </div>

        <div className="col-span-2 bg-panel border border-border rounded-lg p-5 space-y-4">
          <h3 className="font-bold text-white border-b border-border pb-2 flex items-center">
            <Bot className="w-5 h-5 mr-2 text-primary" /> 
            AI Investigation
          </h3>
          
          {tx.investigation ? (
            <div className="space-y-4">
              <div className="p-4 bg-primary/5 border border-primary/20 rounded text-sm text-zinc-300 leading-relaxed">
                {tx.investigation.summary}
              </div>
              <div className="flex items-center justify-between mt-4 border-t border-border pt-4">
                 <div className="text-sm text-zinc-400">Recommendation: <strong className="text-white">{tx.investigation.recommended_action}</strong></div>
                 <div className="space-x-2">
                    <button onClick={() => submitReview('RELEASE')} disabled={reviewing} className="px-3 py-1.5 bg-success/10 text-success rounded text-sm font-bold hover:bg-success/20">RELEASE</button>
                    <button onClick={() => submitReview('CONFIRM_FRAUD')} disabled={reviewing} className="px-3 py-1.5 bg-danger/10 text-danger rounded text-sm font-bold hover:bg-danger/20">CONFIRM FRAUD</button>
                 </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <button 
                onClick={runInvestigation}
                disabled={investigating}
                className="px-6 py-2 bg-primary/10 text-primary font-bold rounded-lg hover:bg-primary/20 transition-colors"
              >
                {investigating ? 'Investigating...' : 'Run Investigation'}
              </button>
            </div>
          )}
        </div>
      </div>
      
      {tx.risk_score && tx.risk_score.reasons && (
        <div className="bg-panel border border-border rounded-lg p-5">
           <h3 className="font-bold text-white mb-4">Evidence & Signals</h3>
           <div className="space-y-2">
             {tx.risk_score.reasons.map((r: any, i: number) => (
                <div key={i} className="flex p-3 bg-zinc-800/50 rounded border border-border">
                  <ShieldAlert className="w-5 h-5 text-warning mr-3 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-bold text-sm text-zinc-200">{r.reason_code}</div>
                    <div className="text-sm text-zinc-400">{r.message}</div>
                  </div>
                </div>
             ))}
           </div>
        </div>
      )}
    </div>
  );
}
""")
print("Wrote transaction pages")
