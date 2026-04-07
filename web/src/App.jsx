import React, { useState, useEffect, useRef, useCallback } from 'react';
import { listConversations, getConversation, createConversation, listAgents, streamChat, createDiscussion } from './api';
import './App.css';

/** 消息气泡 */
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      {msg.agent_name && <span className="message-agent">{msg.agent_name}</span>}
      <div className="message-content">{msg.content}</div>
    </div>
  );
}

/** 角色切换器 */
function AgentSelector({ agents, selected, onChange }) {
  return (
    <div className="agent-selector">
      {agents.map((a) => (
        <button
          key={a.name}
          className={`agent-btn ${selected === a.name ? 'active' : ''}`}
          onClick={() => onChange(a.name)}
          title={a.description}
        >
          @{a.name}
        </button>
      ))}
    </div>
  );
}

/** 讨论模式面板 */
function DiscussionPanel({ onClose }) {
  const [agents, setAgents] = useState([]);
  const [topic, setTopic] = useState('');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [maxRounds, setMaxRounds] = useState(3);
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const wsRef = useRef(null);
  const eventsEndRef = useRef(null);

  useEffect(() => {
    listAgents().then((d) => {
      const agts = d.agents || [];
      setAgents(agts);
      setSelectedAgents(agts.slice(0, 2).map((a) => a.name));
    });
  }, []);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const toggleAgent = (name) => {
    setSelectedAgents((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const startDiscussion = () => {
    if (!topic.trim() || selectedAgents.length === 0) return;
    setRunning(true);
    setEvents([]);

    const ws = createDiscussion(
      { topic, agents: selectedAgents, max_rounds: maxRounds },
      (event) => setEvents((prev) => [...prev, event]),
      () => setRunning(false)
    );
    wsRef.current = ws;
  };

  const stopDiscussion = () => {
    wsRef.current?.close();
    setRunning(false);
  };

  return (
    <div className="panel discussion-panel">
      <div className="panel-header">
        <h2>讨论模式</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="discuss-form">
        <textarea
          className="discuss-topic"
          placeholder="输入讨论主题..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          rows={3}
        />
        <div className="discuss-agents">
          <span className="label">参与角色：</span>
          {agents.map((a) => (
            <button
              key={a.name}
              className={`agent-btn ${selectedAgents.includes(a.name) ? 'active' : ''}`}
              onClick={() => toggleAgent(a.name)}
            >
              {a.name}
            </button>
          ))}
        </div>
        <div className="discuss-options">
          <label>
            轮次：
            <input
              type="number"
              min={1} max={10}
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
            />
          </label>
          {running ? (
            <button className="btn-danger" onClick={stopDiscussion}>停止</button>
          ) : (
            <button className="btn-primary" onClick={startDiscussion} disabled={!topic.trim()}>
              开始讨论
            </button>
          )}
        </div>
      </div>

      <div className="discussion-stream">
        {events.map((e, i) => (
          <div key={i} className="discuss-event">
            <span className={`event-type ${e.type?.replace(/\./g, '_')}`}>
              [{e.type === 'discussion.agent_turn' ? `${e.data?.agent} →` : e.type}]
            </span>
            <span className="event-content">
              {e.data?.token || JSON.stringify(e.data)}
            </span>
          </div>
        ))}
        <div ref={eventsEndRef} />
      </div>
    </div>
  );
}

/** 主 App */
export default function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConv, setCurrentConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('promoter');
  const [showDiscuss, setShowDiscuss] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    listAgents().then((d) => {
      setAgents(d.agents || []);
      if (d.agents?.length > 0) setSelectedAgent(d.agents[0].name);
    });
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    const data = await listConversations();
    setConversations(Array.isArray(data) ? data : []);
  };

  const loadConversation = async (convId) => {
    const data = await getConversation(convId);
    if (data.id) {
      setCurrentConv(data);
      setMessages(data.messages || []);
    }
  };

  const newConversation = async () => {
    const conv = await createConversation('新对话');
    if (conv.id) {
      await loadConversations();
      setCurrentConv({ id: conv.id, title: conv.title, messages: [] });
      setMessages([]);
    }
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const text = input.trim();
    const convId = currentConv?.id;
    setInput('');
    setStreaming(true);

    const userMsg = { id: Date.now(), role: 'user', content: text, agent_name: null };
    const assistantMsg = { id: Date.now() + 1, role: 'assistant', content: '', agent_name: selectedAgent };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    try {
      await streamChat(convId, `@${selectedAgent} ${text}`, {
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) => m.id === assistantMsg.id ? { ...m, content: m.content + token } : m)
          );
        },
        onDone: () => setStreaming(false),
        onError: (err) => {
          setStreaming(false);
          setMessages((prev) =>
            prev.map((m) => m.id === assistantMsg.id ? { ...m, content: `错误: ${err.message}` } : m)
          );
        },
      });
    } catch (e) {
      setStreaming(false);
    }
  }, [input, currentConv, selectedAgent, streaming]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* 侧边栏 */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Council</h1>
          <button className="new-btn" onClick={newConversation}>+ 新对话</button>
        </div>
        <div className="conversation-list">
          {conversations.map((c) => (
            <button
              key={c.id}
              className={`conv-item ${currentConv?.id === c.id ? 'active' : ''}`}
              onClick={() => loadConversation(c.id)}
            >
              {c.title}
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          <button className="discuss-btn" onClick={() => setShowDiscuss(true)}>
            /discuss 讨论模式
          </button>
        </div>
      </aside>

      {/* 主内容 */}
      <main className="main">
        {showDiscuss ? (
          <DiscussionPanel onClose={() => setShowDiscuss(false)} />
        ) : (
          <>
            {agents.length > 0 && (
              <AgentSelector agents={agents} selected={selectedAgent} onChange={setSelectedAgent} />
            )}
            <div className="messages">
              {messages.length === 0 && (
                <div className="empty-state">
                  <p>输入消息开始对话</p>
                  <p className="hint">@角色名 指定角色，/discuss 开启讨论</p>
                </div>
              )}
              {messages.map((m) => <MessageBubble key={m.id} msg={m} />)}
              <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
              <textarea
                ref={inputRef}
                className="chat-input"
                placeholder="输入消息，Enter 发送..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={streaming}
              />
              <button
                className="send-btn"
                onClick={sendMessage}
                disabled={streaming || !input.trim()}
              >
                {streaming ? '●' : '↑'}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
