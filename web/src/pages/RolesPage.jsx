import React, { useState, useEffect } from 'react';
import { Users, Plus, Trash2, X, Pencil } from 'lucide-react';
import { listAgents, listAllModels, updateAgentModel, deleteAgentAPI, createAgentAPI, updateAgentAPI } from '../api';

export default function RolesPage() {
  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', display_name: '', description: '', model_id: '' });
  const [createError, setCreateError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ display_name: '', description: '', system_prompt: '', personality_tone: '', personality_traits: '', model_id: '' });
  const [editError, setEditError] = useState('');

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [aData, mData] = await Promise.all([listAgents(), listAllModels()]);
      // Handle both {agents: [...]} and [...] response formats
      const agentsList = Array.isArray(aData) ? aData : (aData.agents || []);
      const modelsList = Array.isArray(mData) ? mData : (mData.models || []);
      setAgents(agentsList);
      setModels(modelsList);
    } catch (err) {
      console.error('loadData error:', err);
      setAgents([]);
      setModels([]);
    }
    setLoading(false);
  }

  async function handleModelChange(agentId, modelId) {
    try {
      await updateAgentModel(agentId, parseInt(modelId));
      loadData();
    } catch (e) {
      console.warn('Failed to update model:', e);
    }
  }

  async function handleDelete(id) {
    await deleteAgentAPI(id);
    setDeletingId(null);
    loadData();
  }

  async function handleCreate(e) {
    e.preventDefault();
    setCreateError('');
    try {
      await createAgentAPI({ ...createForm, model_id: createForm.model_id || null });
      setCreateModalOpen(false);
      setCreateForm({ name: '', display_name: '', description: '', model_id: '' });
      loadData();
    } catch (err) {
      setCreateError(err.message || 'Failed to create role');
    }
  }

  function openEdit(agent) {
    setEditingId(agent.id);
    setEditForm({
      display_name: agent.display_name || '',
      description: agent.description || '',
      system_prompt: agent.system_prompt || '',
      personality_tone: agent.personality_tone || '',
      personality_traits: Array.isArray(agent.personality_traits) ? agent.personality_traits.join(', ') : (agent.personality_traits || ''),
      model_id: agent.model?.id || agent.model_id || '',
    });
    setEditError('');
  }

  async function handleEdit(e) {
    e.preventDefault();
    setEditError('');
    try {
      const payload = {
        display_name: editForm.display_name,
        description: editForm.description,
        system_prompt: editForm.system_prompt,
        personality_tone: editForm.personality_tone,
        personality_traits: editForm.personality_traits.split(',').map(s => s.trim()).filter(Boolean),
        model_id: editForm.model_id || null,
      };
      await updateAgentAPI(editingId, payload);
      setEditingId(null);
      loadData();
    } catch (err) {
      setEditError(err.message || 'Failed to update role');
    }
  }

  return (
    <div className="p-12">
      <div className="flex justify-between items-end mb-12">
        <div>
          <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface">Committee Roles</h2>
          <p className="text-outline text-lg mt-2">Configure your AI committee members and their models.</p>
        </div>
        <button onClick={() => setCreateModalOpen(true)} className="bg-primary hover:bg-primary-container text-white px-8 py-4 rounded-full font-headline font-bold flex items-center gap-3 transition-all shadow-xl shadow-primary/10">
          <Plus size={20} /> Add Role
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>
      ) : agents.length === 0 ? (
        <div className="text-center py-16 text-outline font-label">No roles configured. Add one to get started.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {agents.map(a => (
            <div key={a.id} className="bg-surface-container-low rounded-lg p-8 flex flex-col gap-6 hover:bg-surface-container-high transition-colors">
              <div className="flex justify-between items-start">
                <div className="w-14 h-14 bg-surface-container-highest rounded-2xl flex items-center justify-center">
                  <Users size={24} className="text-primary" />
                </div>
                <span className="bg-[#d8e2ff] text-[#004395] font-label text-[10px] font-bold px-3 py-1 rounded-full uppercase">Active</span>
              </div>
              <div>
                <h3 className="font-headline text-xl font-bold">{a.name}</h3>
                <p className="text-outline font-label text-xs uppercase">{a.role_type || 'Custom'}</p>
              </div>
              <div>
                <p className="text-outline font-label text-[10px] uppercase tracking-widest mb-2">Model</p>
                <select
                  value={a.model_id || ''}
                  onChange={e => handleModelChange(a.id, e.target.value)}
                  className="w-full bg-white border border-outline-variant/20 rounded-lg px-3 py-2 text-sm font-medium"
                >
                  {models.map(m => (
                    <option key={m.id} value={m.id}>{m.display_name || m.model_name}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button onClick={() => openEdit(a)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:border-primary hover:text-primary transition-all flex items-center justify-center gap-2">
                  <Pencil size={14} /> Edit
                </button>
                <button onClick={() => setDeletingId(a.id)} className="px-3 py-3 border border-outline-variant hover:border-error hover:text-error rounded-full transition-all">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={e => e.target === e.currentTarget && setDeletingId(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <h3 className="font-headline text-xl font-bold mb-2">Delete Role?</h3>
            <p className="text-outline text-sm mb-6">This action cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={() => setDeletingId(null)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:bg-surface-container-low">Cancel</button>
              <button onClick={() => handleDelete(deletingId)} className="flex-1 py-3 bg-error text-white rounded-full font-headline font-bold text-sm hover:opacity-90">Delete</button>
            </div>
          </div>
        </div>
      )}

      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={e => e.target === e.currentTarget && setCreateModalOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-surface-container-high">
              <h3 className="font-headline text-xl font-bold">Add New Role</h3>
              <button onClick={() => setCreateModalOpen(false)} className="text-outline hover:text-on-surface"><X size={20} /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Name (唯一标识)</label>
                <input
                  value={createForm.name}
                  onChange={e => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="e.g. strategist"
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Display Name</label>
                <input
                  value={createForm.display_name}
                  onChange={e => setCreateForm({ ...createForm, display_name: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="e.g. 军师"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Description</label>
                <input
                  value={createForm.description}
                  onChange={e => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="Role description..."
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Model</label>
                <select
                  value={createForm.model_id}
                  onChange={e => setCreateForm({ ...createForm, model_id: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                >
                  <option value="">Default (no model)</option>
                  {models.map(m => (
                    <option key={m.id} value={m.id}>{m.display_name || m.model_name}</option>
                  ))}
                </select>
              </div>
              {createError && <p className="text-error font-label text-sm">{createError}</p>}
              <div className="flex gap-3 mt-2">
                <button type="button" onClick={() => setCreateModalOpen(false)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:bg-surface-container-low">Cancel</button>
                <button type="submit" className="flex-1 py-3 bg-primary text-white rounded-full font-headline font-bold text-sm hover:opacity-90">Create Role</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={e => e.target === e.currentTarget && setEditingId(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-surface-container-high">
              <h3 className="font-headline text-xl font-bold">Edit Role</h3>
              <button onClick={() => setEditingId(null)} className="text-outline hover:text-on-surface"><X size={20} /></button>
            </div>
            <form onSubmit={handleEdit} className="p-6 flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Display Name</label>
                <input
                  value={editForm.display_name}
                  onChange={e => setEditForm({ ...editForm, display_name: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Description</label>
                <input
                  value={editForm.description}
                  onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">System Prompt</label>
                <textarea
                  value={editForm.system_prompt}
                  onChange={e => setEditForm({ ...editForm, system_prompt: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
                  rows={4}
                  placeholder="You are a helpful assistant..."
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Personality Tone</label>
                <input
                  value={editForm.personality_tone}
                  onChange={e => setEditForm({ ...editForm, personality_tone: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="e.g. analytical, direct, empathetic"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Traits (逗号分隔)</label>
                <input
                  value={editForm.personality_traits}
                  onChange={e => setEditForm({ ...editForm, personality_traits: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="strategic, creative, cautious"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1">Model</label>
                <select
                  value={editForm.model_id}
                  onChange={e => setEditForm({ ...editForm, model_id: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                >
                  <option value="">Default (no model)</option>
                  {models.map(m => (
                    <option key={m.id} value={m.id}>{m.display_name || m.model_name}</option>
                  ))}
                </select>
              </div>
              {editError && <p className="text-error font-label text-sm">{editError}</p>}
              <div className="flex gap-3 mt-2">
                <button type="button" onClick={() => setEditingId(null)} className="flex-1 py-3 border border-outline-variant rounded-full font-headline font-bold text-sm hover:bg-surface-container-low">Cancel</button>
                <button type="submit" className="flex-1 py-3 bg-primary text-white rounded-full font-headline font-bold text-sm hover:opacity-90">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
