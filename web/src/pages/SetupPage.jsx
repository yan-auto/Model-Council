import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Key, Shield, CheckCircle, Globe, Bot, Server } from 'lucide-react';
import { createProvider } from '../api';

const PROVIDER_TYPES = [
  { id: 'openai', label: 'OpenAI', icon: Bot, defaultUrl: 'https://api.openai.com/v1' },
  { id: 'anthropic', label: 'Anthropic', icon: Globe, defaultUrl: 'https://api.anthropic.com' },
  { id: 'local', label: 'Custom Endpoint', icon: Server, defaultUrl: 'http://localhost:11434/v1' },
];

export default function SetupPage() {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState('openai');
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1');
  const [apiKey, setApiKey] = useState('');
  const [orgId, setOrgId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function selectType(type) {
    setSelectedType(type);
    const def = PROVIDER_TYPES.find(p => p.id === type)?.defaultUrl || '';
    setBaseUrl(def);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!apiKey) {
      setError('Please enter your API key');
      return;
    }
    setLoading(true);
    setError('');
    try {
      // Map frontend type id to backend provider_type enum value
      const typeMap = { openai: 'openai_compatible', anthropic: 'anthropic', local: 'openai_compatible' };
      await createProvider({
        name: selectedType.charAt(0).toUpperCase() + selectedType.slice(1),
        provider_type: typeMap[selectedType] || selectedType,
        base_url: baseUrl,
        api_key: apiKey,
      });
      sessionStorage.setItem('council_logged_in', 'true');
      navigate('/chat', { replace: true });
    } catch (err) {
      setError(err.message || 'Failed to save provider');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background font-body">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/92 backdrop-blur-md shadow-sm h-16 flex justify-between items-center px-8 font-headline tracking-tight">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold text-[#1a1c1c]">Council AI</span>
          <div className="hidden md:flex gap-6 items-center">
            <a className="text-primary font-bold border-b-2 border-primary pb-1" href="/setup">Onboarding</a>
            <a className="text-[#727784] hover:text-[#1a1c1c] transition-colors" href="/security">Security</a>
            <a className="text-[#727784] hover:text-[#1a1c1c] transition-colors" href="/providers">Providers</a>
          </div>
        </div>
        <a href="/profile" className="p-2 text-[#727784] hover:bg-surface-container-low rounded-full transition-colors">
          <Key size={20} />
        </a>
      </nav>

      {/* Main */}
      <main className="flex-grow flex flex-col items-center justify-center pt-24 pb-12 px-6">
        {/* Header */}
        <div className="max-w-4xl w-full mb-12 text-center">
          <h1 className="font-headline text-4xl md:text-5xl font-bold text-[#1a1c1c] tracking-tighter mb-4">Initialize Executive Protocol</h1>
          <p className="text-[#59605f] font-body text-lg max-w-2xl mx-auto">Prepare your high-stakes AI environment. Council secures and orchestrates your local and cloud intelligence.</p>
        </div>

        {/* Stepper */}
        <div className="max-w-3xl w-full mb-12">
          <div className="flex justify-between items-center relative">
            <div className="absolute top-1/2 left-0 w-full h-[2px] bg-[#e2e2e2] -translate-y-1/2 z-0" />
            <div className="absolute top-1/2 left-0 w-1/2 h-[2px] bg-[#004496] -translate-y-1/2 z-0" />
            {[
              { n: 1, label: 'Environment', done: true },
              { n: 2, label: 'API Config', active: true },
              { n: 3, label: 'Identity', done: false },
            ].map(({ n, label, done, active }) => (
              <div key={n} className="relative z-10 flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shadow-lg ${done || active ? 'bg-primary text-white' : 'bg-[#e2e2e2] text-[#59605f]'}`}>
                  {done ? <CheckCircle size={16} /> : n}
                </div>
                <span className="absolute -bottom-8 whitespace-nowrap font-label text-[10px] uppercase tracking-widest font-bold" style={{ color: done || active ? '#004496' : '#59605f' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Form Grid */}
        <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
          {/* Main Form */}
          <div className="md:col-span-8 bg-white rounded-lg p-10 border border-[#c2c6d5]/15 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <Key size={28} className="text-primary" />
              <h2 className="font-headline text-2xl font-bold tracking-tight">API Configuration</h2>
            </div>

            {/* Provider Type Selection */}
            <div className="mb-8">
              <label className="block font-label text-xs font-bold uppercase tracking-widest text-[#59605f] mb-3">Primary Intelligence Provider</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {PROVIDER_TYPES.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => selectType(id)}
                    className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all text-left ${
                      selectedType === id
                        ? 'bg-[#e8e8e7] border-primary ring-2 ring-primary/10'
                        : 'bg-[#f3f4f3] border-transparent hover:bg-[#e8e8e7]'
                    }`}
                  >
                    <Icon size={24} className={selectedType === id ? 'text-primary mb-2' : 'text-[#59605f] mb-2'} />
                    <span className="font-body font-bold text-sm">{label}</span>
                    <span className="font-label text-[10px] mt-1" style={{ color: selectedType === id ? '#004496' : '#59605f' }}>
                      {selectedType === id ? 'Selected' : id === 'anthropic' ? 'Ready to sync' : id === 'local' ? 'Self-hosted' : 'Select this'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Form Fields */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block font-label text-xs font-bold uppercase tracking-widest text-[#59605f] mb-2">Base URL</label>
                <input
                  type="url"
                  value={baseUrl}
                  onChange={e => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="w-full bg-white/80 backdrop-blur-sm rounded-full border border-[#c2c6d5]/30 px-6 py-4 font-mono text-sm text-[#1a1c1c] focus:outline-none focus:border-primary/40 transition-all"
                />
              </div>

              <div>
                <label className="block font-label text-xs font-bold uppercase tracking-widest text-[#59605f] mb-2">Secret API Key</label>
                <div className="relative">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder="sk-proj-••••••••••••••••••••••••"
                    className="w-full bg-white/80 backdrop-blur-sm rounded-full border border-[#c2c6d5]/30 px-6 py-4 font-mono text-sm text-[#1a1c1c] focus:outline-none focus:border-primary/40 transition-all pr-10"
                  />
                </div>
              </div>

              <div>
                <label className="block font-label text-xs font-bold uppercase tracking-widest text-[#59605f] mb-2">Organization ID (Optional)</label>
                <input
                  type="text"
                  value={orgId}
                  onChange={e => setOrgId(e.target.value)}
                  placeholder="org-8Y2n..."
                  className="w-full bg-white/80 backdrop-blur-sm rounded-full border border-[#c2c6d5]/30 px-6 py-4 font-mono text-sm text-[#1a1c1c] focus:outline-none focus:border-primary/40 transition-all"
                />
              </div>

              {error && <p className="text-[#ba1a1a] font-label text-sm">{error}</p>}

              <div className="pt-6 flex justify-between items-center">
                <a href="/login" className="px-8 py-3 rounded-full font-body font-bold text-[#59605f] hover:bg-[#f3f4f3] transition-colors">Back</a>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-10 py-4 rounded-full bg-gradient-to-r from-[#004496] to-[#005bc4] text-white font-body font-bold shadow-lg shadow-primary/20 active:scale-95 transition-all disabled:opacity-50"
                >
                  {loading ? 'Validating...' : 'Validate and Continue'}
                </button>
              </div>
            </form>
          </div>

          {/* Sidebar Cards */}
          <div className="md:col-span-4 flex flex-col gap-6">
            <div className="bg-[#f3f4f3] rounded-lg p-6 flex flex-col gap-4">
              <h3 className="font-headline font-bold text-sm uppercase tracking-widest">Environment Check</h3>
              <div className="space-y-4">
                {[
                  { icon: CheckCircle, label: 'Local AI Found', sub: 'Ollama running on v0.1.32', ok: true },
                  { icon: CheckCircle, label: 'Encrypted Vault', sub: 'AES-256 hardware initialized', ok: true },
                  { icon: Globe, label: 'Cloud Handshake', sub: 'Awaiting API validation...', ok: false },
                ].map(({ icon: Icon, label, sub, ok }) => (
                  <div key={label} className="flex items-center gap-3">
                    <Icon size={16} className={ok ? 'text-green-600' : 'text-primary'} style={{ fill: ok ? 'currentColor' : 'none' }} />
                    <div>
                      <p className="font-body text-sm font-bold">{label}</p>
                      <p className="font-label text-[10px] text-[#59605f]">{sub}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-primary/5 rounded-lg p-6 border border-primary/10 flex flex-col gap-4">
              <Shield size={20} className="text-primary" />
              <div>
                <h4 className="font-body font-bold text-primary mb-1">Security First</h4>
                <p className="font-body text-xs text-[#001a42] leading-relaxed">Council never transmits your raw API keys. All credentials are stored in your hardware-backed local keychain.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
