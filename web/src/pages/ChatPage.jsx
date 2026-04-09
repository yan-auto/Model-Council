import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Sparkles, AlertTriangle, BarChart3, Send, Loader2, Image, X
} from 'lucide-react';
import { listConversations, createConversation, listAgents, streamChat, getConversation } from '../api';

function formatTime(dateVal) {
  if (!dateVal) return '';
  const ms = typeof dateVal === 'number' ? (dateVal > 1e12 ? dateVal : dateVal * 1000) : new Date(dateVal).getTime();
  return new Date(ms).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  const name = isUser ? '你' : (msg.agent_name || 'Council');
  const color = isUser ? '#004496' : '#757c7b';
  const bg = isUser ? 'bg-[#004496] text-white' : 'bg-[#e8e8e7] text-[#1a1c1c]';
  return (
    <div className={`flex gap-3 animate-fadeIn ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1" style={{ background: color }}>
        {name.slice(0, 1)}
      </div>
      <div className={`flex flex-col gap-1 max-w-[70%] ${isUser ? 'items-end' : ''}`}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold" style={{ color }}>{name}</span>
          <span className="text-[10px] text-[#727784]">{formatTime(msg.created_at)}</span>
        </div>
        {msg.image_data && (
          <img
            src={msg.image_data}
            alt="attachment"
            className="max-w-[200px] rounded-lg mb-1 cursor-pointer hover:opacity-90"
            onClick={() => window.open(msg.image_data, '_blank')}
          />
        )}
        <div className={`${bg} px-4 py-3 rounded-2xl text-sm leading-relaxed`}>{msg.content}</div>
      </div>
    </div>
  );
}

function StreamingBubble({ agentName, content }) {
  return (
    <div className="flex gap-3 animate-fadeIn">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1 bg-[#757c7b]">
        {(agentName || 'C').slice(0, 1)}
      </div>
      <div className="flex flex-col gap-1 max-w-[70%]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[#757c7b]">{agentName || 'Council'}</span>
          <span className="text-[10px] text-[#727784]">typing...</span>
        </div>
        <div className="bg-[#e8e8e7] px-4 py-3 rounded-2xl text-sm leading-relaxed text-[#1a1c1c]">{content}</div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [convs, setConvs] = useState([]);
  const [agents, setAgents] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingAgent, setStreamingAgent] = useState('');
  const [selectedImage, setSelectedImage] = useState(null); // base64 data URL

  const inputRef = useRef(null);
  const bottomRef = useRef(null);
  const imageInputRef = useRef(null);

  // Auth guard
  useEffect(() => {
    if (sessionStorage.getItem('council_logged_in') !== 'true') {
      navigate('/login');
    }
  }, []);

  useEffect(() => {
    listAgents().then(d => setAgents(d.agents || [])).catch(() => {});
    listConversations().then(d => setConvs(Array.isArray(d) ? d : d.conversations || [])).catch(() => {});
  }, []);

  // Load conversation from navigation state (HistoryPage click)
  useEffect(() => {
    const convId = location.state?.convId;
    if (convId) {
      setCurrentConvId(convId);
      getConversation(convId).then(d => {
        const msgs = d.messages || [];
        setMessages(msgs.map(m => ({
          role: m.role === 'assistant' ? 'assistant' : 'user',
          content: m.content,
          agent_name: m.agent_name,
          image_data: m.image_data || null,
          created_at: m.created_at,
        })));
      }).catch(() => {});
    }
  }, [location.state]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  function handleInput() {
    const el = inputRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 150) + 'px';
    }
  }

  async function handleSend() {
    if (streaming) return;
    const text = input.trim();
    if (!text && !selectedImage) return;

    const image = selectedImage;
    setInput('');
    setSelectedImage(null);
    setStreaming(true);
    setStreamingContent('');
    setStreamingAgent('');

    let convId = currentConvId;
    if (!convId) {
      const conv = await createConversation(text.slice(0, 30));
      convId = conv.id;
      setCurrentConvId(convId);
      listConversations().then(d => setConvs(Array.isArray(d) ? d : d.conversations || [])).catch(() => {});
    }

    const userMsg = { role: 'user', content: text || '[图片]', image_data: image, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);

    let currentAgent = '';
    let currentContent = '';

    await streamChat(convId, text, {
      imageData: image,
      onToken: (token, agent) => {
        if (agent) {
          currentAgent = agent;
          setStreamingAgent(agent);
        }
        if (token) {
          currentContent += token;
          setStreamingContent(currentContent);
        }
      },
      onDone: () => {
        const assistantMsg = { role: 'assistant', agent_name: currentAgent || 'Council', content: currentContent, created_at: new Date().toISOString() };
        setMessages(prev => [...prev, assistantMsg]);
        setStreaming(false);
        setStreamingContent('');
        setStreamingAgent('');
      },
      onError: (err) => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          agent_name: 'Council',
          content: `错误: ${err.message}`,
          created_at: new Date().toISOString()
        }]);
        setStreaming(false);
        setStreamingContent('');
        setStreamingAgent('');
      }
    });
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 pb-48 flex flex-col">
        {messages.length === 0 && (
          <div className="my-auto flex flex-col items-center justify-center max-w-2xl mx-auto py-12">
            <div className="mb-8 p-8 bg-[#e8e8e7] rounded-[3rem] shadow-sm">
              <Sparkles size={56} className="text-[#004496]" />
            </div>
            <h2 className="font-headline font-bold text-4xl text-[#1a1c1c] mb-4 text-center tracking-tight">The Council is Ready</h2>
            <p className="font-body text-[#727784] text-center mb-10 max-w-md leading-relaxed">Your executive AI committee is synchronized and awaiting instructions.</p>
            <div className="flex flex-wrap justify-center gap-3">
              <button
                onClick={() => { setInput('帮我分析一下当前的风险'); inputRef.current?.focus(); }}
                className="px-5 py-2.5 bg-[#e8e8e7] hover:bg-[#c2c6d5]/30 transition-all active:scale-95 rounded-full text-sm font-label font-medium flex items-center gap-2 text-[#1a1c1c]"
              >
                <AlertTriangle size={16} className="text-[#004496]" />Help me prioritize
              </button>
              <button
                onClick={() => { setInput('分析一下风险'); inputRef.current?.focus(); }}
                className="px-5 py-2.5 bg-[#e8e8e7] hover:bg-[#c2c6d5]/30 transition-all active:scale-95 rounded-full text-sm font-label font-medium flex items-center gap-2 text-[#1a1c1c]"
              >
                <BarChart3 size={16} className="text-[#004496]" />Analyze the risks
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {streaming && streamingContent && (
          <StreamingBubble agentName={streamingAgent} content={streamingContent} />
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="px-6 pb-6">
        <div className="max-w-4xl mx-auto relative">
          {/* Image Preview */}
          {selectedImage && (
            <div className="mb-2 flex items-center gap-2">
              <div className="relative inline-block">
                <img src={selectedImage} alt="preview" className="max-h-24 rounded-lg border border-[#e4e9e8]" />
                <button
                  onClick={() => setSelectedImage(null)}
                  className="absolute -top-2 -right-2 w-5 h-5 bg-[#ba1a1a] text-white rounded-full flex items-center justify-center hover:opacity-80"
                >
                  <X size={12} />
                </button>
              </div>
              <span className="text-[10px] text-[#727784] font-label">Image attached</span>
            </div>
          )}
          <div className="glass-panel border border-white/40 shadow-[0_20px_40px_rgba(45,52,51,0.06)] rounded-[2.5rem] p-3 flex flex-col gap-2">
            <div className="flex items-center gap-3 px-2">
              {/* Image Upload */}
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const reader = new FileReader();
                  reader.onload = ev => setSelectedImage(ev.target.result);
                  reader.readAsDataURL(file);
                  e.target.value = '';
                }}
              />
              <button
                onClick={() => imageInputRef.current?.click()}
                className="w-10 h-10 flex items-center justify-center text-[#727784] hover:text-[#004496] transition-colors shrink-0"
                disabled={streaming}
              >
                <Image size={20} />
              </button>
              <textarea
                id="chat-input"
                ref={inputRef}
                value={input}
                onChange={e => { setInput(e.target.value); handleInput(); }}
                onKeyDown={handleKeyDown}
                placeholder="Direct the Council..."
                disabled={streaming}
                className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-medium font-body placeholder:text-[#727784] py-3 px-4 resize-none"
                rows={1}
              />
              <button
                onClick={handleSend}
                disabled={streaming || (!input.trim() && !selectedImage)}
                className="w-12 h-12 bg-[#004496] text-white rounded-full flex items-center justify-center shadow-lg shadow-[#004496]/20 hover:brightness-110 active:scale-90 transition-all disabled:opacity-50"
              >
                {streaming ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
            <div className="flex items-center justify-between px-4 pb-1 border-t border-[#e8e8e7] pt-2">
              <div className="flex items-center gap-4">
                <button className="text-[10px] font-bold font-label text-[#727784] hover:text-[#004496] flex items-center gap-1.5 uppercase tracking-tighter transition-colors active:scale-95">
                  <Sparkles size={14} />Parameters
                </button>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-[10px] font-black font-label text-[#727784] uppercase tracking-widest">Protocol Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
