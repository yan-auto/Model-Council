import React from 'react';
import { Terminal } from 'lucide-react';

export default function LogsPage() {
  return (
    <div className="p-12">
      <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface mb-4">System Logs</h2>
      <p className="text-outline text-lg mb-12">Monitor system activity and events.</p>

      <div className="bg-surface-container-low rounded-lg p-8 max-w-4xl">
        <div className="flex items-center gap-3 mb-4">
          <Terminal size={20} className="text-outline" />
          <span className="font-label text-sm font-bold text-outline uppercase tracking-widest">Recent Activity</span>
        </div>
        <div className="space-y-2 font-mono text-sm text-outline">
          <p>[2026-04-08 12:00:00] System initialized</p>
          <p>[2026-04-08 12:00:01] API gateway ready on port 8000</p>
          <p>[2026-04-08 12:00:02] Database connection established</p>
          <p className="text-outline/50">[2026-04-08 12:00:05] Waiting for connections...</p>
        </div>
        <p className="text-outline font-label text-sm mt-6">Backend logging integration coming soon.</p>
      </div>
    </div>
  );
}
