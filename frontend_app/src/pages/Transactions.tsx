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
