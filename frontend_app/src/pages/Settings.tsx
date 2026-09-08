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
