import React from 'react';
import { MessageSquare } from 'lucide-react';

export default function ChatDetailsPage() {
  return (
    <div className="p-12">
      <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface mb-4">Chat Details</h2>
      <p className="text-outline text-lg mb-12">Review feedback and outcomes from your AI discussions.</p>

      <div className="bg-surface-container-low rounded-lg p-8 max-w-4xl flex items-center gap-4">
        <MessageSquare size={32} className="text-outline" />
        <div>
          <p className="font-headline font-bold">Feedback System</p>
          <p className="text-outline text-sm">Rate responses and provide feedback to improve the AI committee.</p>
        </div>
      </div>
    </div>
  );
}
