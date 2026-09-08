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
