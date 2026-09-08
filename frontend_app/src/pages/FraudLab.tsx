import { useState } from 'react';
import api from '../services/api';
import { ShieldAlert, Play } from 'lucide-react';

export default function FraudLab() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const launchAttack = async (type: string, size: number) => {
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
