import { useState } from 'react';
import ReactFlow, { Background, Controls, useNodesState, useEdgesState } from 'reactflow';
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
      
      const newNodes = res.data.nodes.map((n: any) => ({
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
