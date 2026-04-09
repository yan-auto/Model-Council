import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock } from 'lucide-react';

export default function SecurityPage() {
  const navigate = useNavigate();

  function handleLogout() {
    sessionStorage.removeItem('council_logged_in');
    navigate('/login');
  }

  return (
    <div className="p-12">
      <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface mb-4">Security & Privacy</h2>
      <p className="text-outline text-lg mb-12">Manage your security settings and privacy preferences.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl">
        <div className="bg-surface-container-low rounded-lg p-8">
          <Shield size={24} className="text-primary mb-4" />
          <h3 className="font-headline text-xl font-bold mb-2">Session Security</h3>
          <p className="text-outline text-sm">All sessions are encrypted with AES-256. Your data never leaves your local environment.</p>
        </div>
        <div className="bg-surface-container-low rounded-lg p-8">
          <Lock size={24} className="text-primary mb-4" />
          <h3 className="font-headline text-xl font-bold mb-2">API Keys</h3>
          <p className="text-outline text-sm">Your API keys are stored locally and never transmitted raw to third parties.</p>
        </div>
      </div>

      <div className="mt-16">
        <button onClick={handleLogout} className="text-error font-label text-sm hover:underline">Sign out of all sessions</button>
      </div>
    </div>
  );
}
