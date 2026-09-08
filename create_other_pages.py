import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

write_file("frontend_app/src/pages/FraudNetwork.tsx", """
import { useState, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';
import api from '../services/api';

export default function FraudNetwork() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [entityId, setEntityId] = useState('CUST_e40ffe95');
  const [loading, setLoading] = useState(false);

  const fetchGraph = async () => {
    if (!entityId) return;
    setLoading(true);
    try {
      const res = await api.get(`/graph/entity/${entityId}`);
      
      const newNodes = res.data.nodes.map((n: any, idx: number) => ({
        id: n.id,
        data: { label: n.data.label },
        position: { x: Math.random() * 400, y: Math.random() * 400 },
        style: { 
          background: n.data.type === 'CUSTOMER' ? '#3b82f6' : 
                      n.data.type === 'DEVICE' ? '#f59e0b' : 
                      n.data.type === 'IP' ? '#ef4444' : '#10b981',
          color: 'white',
          border: 'none',
          borderRadius: n.data.type === 'TRANSACTION' ? '50%' : '8px',
          padding: '10px'
        }
      }));
      
      const newEdges = res.data.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: true,
        style: { stroke: '#52525b' }
      }));
      
      setNodes(newNodes);
      setEdges(newEdges);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex space-x-4 shrink-0">
        <input 
          type="text" 
          value={entityId} 
          onChange={e => setEntityId(e.target.value)} 
          placeholder="Enter Entity ID (e.g. CUST_...)"
          className="bg-panel border border-border rounded px-4 py-2 w-64 text-sm focus:outline-none focus:border-primary"
        />
        <button 
          onClick={fetchGraph} 
          disabled={loading}
          className="px-4 py-2 bg-primary text-white rounded font-bold text-sm"
        >
          {loading ? 'Loading...' : 'Load Network'}
        </button>
      </div>
      
      <div className="flex-1 bg-panel border border-border rounded-lg overflow-hidden">
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodesChange={onNodesChange} 
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Background color="#27272a" />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
""")

write_file("frontend_app/src/pages/Models.tsx", """
import { useState, useEffect } from 'react';
import api from '../services/api';

export default function Models() {
  const [models, setModels] = useState<any[]>([]);

  useEffect(() => {
    api.get('/models').then(res => setModels(res.data.data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white">Models</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((m, idx) => (
          <div key={idx} className="bg-panel border border-border rounded-lg p-5">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-white">{m.model_type}</h3>
                <p className="text-zinc-500 text-sm">v{m.version}</p>
              </div>
              {m.is_active && <span className="bg-success/10 text-success text-xs px-2 py-1 rounded font-bold">ACTIVE</span>}
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-zinc-500 block">ROC-AUC</span><span className="text-white font-mono">{m.roc_auc.toFixed(4)}</span></div>
              <div><span className="text-zinc-500 block">PR-AUC</span><span className="text-white font-mono">{m.pr_auc.toFixed(4)}</span></div>
              <div><span className="text-zinc-500 block">Precision</span><span className="text-white font-mono">{m.precision.toFixed(4)}</span></div>
              <div><span className="text-zinc-500 block">Recall</span><span className="text-white font-mono">{m.recall.toFixed(4)}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
""")

write_file("frontend_app/src/pages/Settings.tsx", """
export default function Settings() {
  return (
    <div className="space-y-4 max-w-2xl">
      <h2 className="text-2xl font-bold text-white">Settings</h2>
      <div className="bg-panel border border-border rounded-lg p-5 text-zinc-400">
        <p>Settings configuration panel. Risk Weights and Thresholds can be managed here in a future update.</p>
        <p className="mt-4 text-sm text-warning">Current Configuration is managed via environment variables.</p>
      </div>
    </div>
  );
}
""")

write_file("frontend_app/src/pages/AuditLog.tsx", """
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
""")
print("Wrote remaining pages")
