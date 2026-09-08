import { useState, useEffect } from 'react';
import api from '../services/api';

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    api.get('/audit-log?limit=50').then(res => setLogs(res.data.data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white">Audit Log</h2>
      <div className="bg-panel border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-800/50 text-zinc-400">
            <tr>
              <th className="px-6 py-3 font-medium">Time</th>
              <th className="px-6 py-3 font-medium">Action</th>
              <th className="px-6 py-3 font-medium">Actor</th>
              <th className="px-6 py-3 font-medium">Transaction</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {logs.map((log, i) => (
              <tr key={i} className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-6 py-3 text-zinc-500">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-6 py-3 font-mono text-zinc-300">{log.action}</td>
                <td className="px-6 py-3 text-white">{log.actor}</td>
                <td className="px-6 py-3 font-mono text-xs text-zinc-400">{log.transaction_id?.split('-')[0]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
