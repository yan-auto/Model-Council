import React, { useState, useEffect } from 'react';
import { Building2, Plus, X, CheckCircle } from 'lucide-react';
import { listProviders, createProvider, updateProvider, deleteProvider } from '../api';

export default function ProvidersPage() {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: '', type: 'openai', base_url: '', api_key: '' });
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => { loadProviders(); }, []);

  async function loadProviders() {
    setLoading(true);
    try {
      const data = await listProviders();
      setProviders(data.providers || []);
    } catch { setProviders([]); }
    setLoading(false);
  }

  function openAdd() {
    setEditingId(null);
    setForm({ name: '', type: 'openai', base_url: 'https://api.openai.com/v1', api_key: '' });
    setError('');
    setModalOpen(true);
  }

  function openEdit(p) {
    setEditingId(p.id);
    setForm({ name: p.name || '', type: p.type || 'openai', base_url: p.base_url || '', api_key: p.api_key || '' });
    setError('');
    setModalOpen(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (editingId) {
        await updateProvider(editingId, form);
      } else {
        await createProvider(form);
      }
      setModalOpen(false);
      loadProviders();
    } catch (err) {
      setError(err.message || 'Failed to save');
    }
  }

  async function handleDelete(id) {
    await deleteProvider(id);
    setDeletingId(null);
    loadProviders();
  }

  return (
    <div className="p-12">
      {/* Header */}
      <div className="flex justify-between items-end mb-16">
        <div>
          <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface">Suppliers</h2>
          <p className="text-outline text-lg max-w-xl mt-2">Provision and manage high-fidelity intelligence sources for your Executive Protocol.</p>
        </div>
        <button onClick={openAdd} className="bg-primary hover:bg-primary-container text-white px-8 py-4 rounded-full font-headline font-bold flex items-center gap-3 transition-all shadow-xl shadow-primary/10">
          <Plus size={20} /> Add New Provider
        </button>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20"><div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>
      ) : providers.length === 0 ? (
        <div className="text-center py-16 text-outline font-label">No providers configured. Add one to get started.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {providers.map(p => (
            <div key={p.id} className="bg-surface-container-low rounded-lg p-8 flex flex-col justify-between group hover:bg-surface-container-high transition-colors">
              <div>
                <div className="flex justify-between items-start mb-8">
                  <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-sm">
                    <Building2 size={24} className="text-primary" />
                  </div>
                  <span className="bg-emerald-100 text-emerald-700 font-label text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1.5 uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                    {p.status || 'Healthy'}
                  </span>
                </div>
                <h3 className="font-headline text-2xl font-bold mb-1">{p.name}</h3>
                <p className="text-outline font-label text-xs uppercase mb-6 tracking-wide">
                  {p.provider_type === 'openai_compatible' ? 'Cloud Provider' : p.provider_type === 'anthropic' ? 'Anthropic' : p.provider_type === 'minimax' ? 'MiniMax' : 'Custom'}
                </p>
                <div className="space-y-6">
                  <div>
                    <p className="text-outline font-label text-[10px] uppercase tracking-widest mb-2">Base URL</p>
                    <p className="font-mono text-xs text-[#727784] truncate">{p.base_url || '—'}</p>
                  </div>
                </div>
              </div>
              <div className="mt-10 flex gap-2">
                <button onClick={() => openEdit(p)} className="flex-1 py-3 border border-outline-variant hover:border-primary hover:text-primary rounded-full font-headline font-bold text-sm transition-all">Manage</button>
                <button onClick={() => setDeletingId(p.id)} className="px-3 py-3 border border-outline-variant hover:border-error hover:text-error rounded-full transition-all">
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={e => e.target === e.currentTarget && setModalOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-surface-container-high">
              <h3 className="font-headline text-xl font-bold">{editingId ? 'Edit Provider' : 'Add New Provider'}</h3>
              <button onClick={() => setModalOpen(false)} className="text-outline hover:text-on-surface"><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Provider Name</label>
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all" placeholder="OpenAI, Anthropic, etc." required />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Type</label>
                <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })} className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all">
                  <option value="openai">OpenAI Compatible</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google AI</option>
                  <option value="local">Local / On-Premise</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Base URL</label>
                <input value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all" placeholder="https://api.openai.com/v1" required />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">API Key</label>
                <input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all" placeholder="sk-..." required />
              </div>
              {error && <p className="text-error font-label text-sm">{error}</p>}
              <div className="flex gap-3 mt-2">
                <button type="button" onClick={() => setModalOpen(false)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:bg-surface-container-low">Cancel</button>
                <button type="submit" className="flex-1 py-3 bg-primary text-white rounded-full font-headline font-bold text-sm hover:opacity-90">Save Provider</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirm */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={e => e.target === e.currentTarget && setDeletingId(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <h3 className="font-headline text-xl font-bold mb-2">Delete Provider?</h3>
            <p className="text-outline text-sm mb-6">This action cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={() => setDeletingId(null)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:bg-surface-container-low">Cancel</button>
              <button onClick={() => handleDelete(deletingId)} className="flex-1 py-3 bg-error text-white rounded-full font-headline font-bold text-sm hover:opacity-90">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
