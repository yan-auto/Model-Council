import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings, LogOut } from 'lucide-react';
import { getProfile, updateProfile } from '../api';

export default function ProfilePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', background: '', constraints: '' });
  const [orig, setOrig] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProfile().then(d => {
      const u = d.user || {};
      const data = { name: u.name || '', background: u.background || '', constraints: u.constraints || '' };
      setForm(data);
      setOrig(data);
    }).catch(() => {});
  }, []);

  function handleDiscard() {
    setForm(orig);
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updateProfile(form);
      setOrig(form);
    } catch {}
    setSaving(false);
  }

  return (
    <div className="max-w-4xl mx-auto px-12 py-16">
      <div className="mb-12">
        <h2 className="font-headline text-5xl font-bold tracking-tighter text-on-surface mb-2">Protocol Settings</h2>
        <p className="text-outline text-lg">Define your operational parameters and strategic alignment for the Council.</p>
      </div>

      <div className="space-y-16">
        {/* Identity */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1">
            <h3 className="font-headline text-xl font-bold tracking-tight">Identity</h3>
            <p className="text-outline text-sm mt-1">Your core profile used by the AI committee to frame all responses.</p>
          </div>
          <div className="md:col-span-2 space-y-6">
            <div className="bg-surface-container-low p-8 rounded-lg space-y-6">
              <div className="group">
                <label className="font-label text-[10px] uppercase tracking-widest text-outline mb-2 block">Name</label>
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full bg-transparent border-none p-0 text-xl font-headline font-medium focus:ring-0 text-on-surface" />
              </div>
              <div className="group">
                <label className="font-label text-[10px] uppercase tracking-widest text-outline mb-2 block">Background</label>
                <textarea value={form.background} onChange={e => setForm({ ...form, background: e.target.value })} className="w-full bg-transparent border-none p-0 text-body text-on-surface focus:ring-0 resize-none leading-relaxed" rows={4} />
              </div>
            </div>
          </div>
        </div>

        {/* Strategy */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1">
            <h3 className="font-headline text-xl font-bold tracking-tight">Strategy</h3>
            <p className="text-outline text-sm mt-1">Primary objectives and operational limits.</p>
          </div>
          <div className="md:col-span-2 space-y-8">
            <div className="bg-surface-container-low p-8 rounded-lg space-y-6">
              <div className="group">
                <label className="font-label text-[10px] uppercase tracking-widest text-outline mb-2 block">Constraints</label>
                <textarea value={form.constraints} onChange={e => setForm({ ...form, constraints: e.target.value })} className="w-full bg-transparent border-none p-0 text-body text-on-surface focus:ring-0 resize-none" rows={2} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Bar */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-white/92 backdrop-blur-md p-2 rounded-full border border-outline-variant/10 shadow-xl flex gap-4 pr-6">
        <button onClick={handleSave} disabled={saving} className="bg-primary hover:bg-primary-container text-white font-headline font-bold px-12 py-4 rounded-full transition-all shadow-lg shadow-primary/20 flex items-center gap-3">
          <Settings size={18} /> {saving ? 'Saving...' : 'Save Protocol Changes'}
        </button>
        <button onClick={handleDiscard} className="text-outline font-label text-sm px-4 hover:text-on-surface transition-colors">Discard</button>
      </div>
    </div>
  );
}
