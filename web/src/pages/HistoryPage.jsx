import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Archive, ChevronRight } from 'lucide-react';
import { listConversations } from '../api';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [convs, setConvs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listConversations('active')
      .then(d => setConvs(Array.isArray(d) ? d : d.conversations || []))
      .catch(() => setConvs([]))
      .finally(() => setLoading(false));
  }, []);

  function formatDate(dateVal) {
    if (!dateVal) return '';
    const ms = typeof dateVal === 'number' ? (dateVal > 1e12 ? dateVal : dateVal * 1000) : new Date(dateVal).getTime();
    return new Date(ms).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  return (
    <div className="max-w-4xl mx-auto px-12 py-16">
      <div className="flex justify-between items-end mb-12">
        <div>
          <h2 className="font-headline text-5xl font-bold tracking-tight text-on-surface mb-2">Chat History</h2>
          <p className="text-outline text-lg">Manage and review previous executive sessions.</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>
      ) : convs.length === 0 ? (
        <div className="text-center py-16 text-outline font-label">No conversations yet.</div>
      ) : (
        <div className="space-y-4">
          {convs.map(c => (
            <div
              key={c.id}
              onClick={() => navigate('/chat', { state: { convId: c.id } })}
              className="bg-surface-container-low p-6 rounded-xl flex justify-between items-center hover:bg-surface-container-high transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center text-primary">
                  <Archive size={18} />
                </div>
                <div>
                  <h5 className="font-body font-bold text-on-surface">{c.title || 'Untitled'}</h5>
                  <p className="text-xs text-outline font-label">{formatDate(c.updated_at)}</p>
                </div>
              </div>
              <ChevronRight size={20} className="text-outline" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
