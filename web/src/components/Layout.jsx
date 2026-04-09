import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Plus, MessageSquare, Users, Building2, Settings,
  LogOut, Archive, Clock, ChevronLeft, Search, Bell,
  Star, Shield, Terminal
} from 'lucide-react';
import { listConversations, listAgents } from '../api';

const NAV_ITEMS = [
  { to: '/history', icon: MessageSquare, label: 'Chat History' },
  { to: '/roles', icon: Users, label: 'Role Management' },
  { to: '/providers', icon: Building2, label: 'Suppliers' },
  { to: '/logs', icon: Terminal, label: 'System Logs' },
  { to: '/archive', icon: Archive, label: 'Archive' },
];

export default function Layout({ children }) {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [convs, setConvs] = useState([]);
  const [agents, setAgents] = useState([]);
  const [activeAgent, setActiveAgent] = useState(null);

  useEffect(() => {
    if (sessionStorage.getItem('council_logged_in') !== 'true') {
      navigate('/login');
      return;
    }
    loadData();
  }, []);

  async function loadData() {
    try {
      const [convData, agentData] = await Promise.all([
        listConversations(),
        listAgents(),
      ]);
      setConvs(convData.conversations || []);
      setAgents(agentData.agents || []);
    } catch (e) {
      console.warn('Failed to load data:', e);
    }
  }

  function handleLogout() {
    sessionStorage.removeItem('council_logged_in');
    navigate('/login');
  }

  function handleNewChat() {
    navigate('/chat');
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={`h-full bg-[#f3f4f3] flex flex-col transition-all duration-300 ease-in-out z-50 relative shrink-0 ${collapsed ? 'w-[80px]' : 'w-[260px]'}`}
      >
        {/* Header */}
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white shrink-0">
              <Shield size={20} />
            </div>
            {!collapsed && (
              <div>
                <h1 className="font-headline font-black tracking-tight text-xl text-primary whitespace-nowrap">The Council</h1>
                <p className="text-[10px] uppercase tracking-widest text-outline font-bold">Executive Protocol</p>
              </div>
            )}
          </div>

          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="w-full bg-primary text-white rounded-full py-3.5 flex items-center justify-center gap-2 font-bold font-headline transition-all active:scale-95 hover:brightness-110 shadow-lg shadow-primary/20 mb-6"
          >
            <Plus size={18} />
            {!collapsed && <span className="whitespace-nowrap">New Chat</span>}
          </button>

          {/* Nav */}
          <nav className="flex-1 overflow-y-auto no-scrollbar min-h-0">
            {!collapsed && (
              <p className="text-[10px] font-bold text-outline px-4 mb-4 uppercase tracking-widest">Menu</p>
            )}
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 ${collapsed ? 'justify-center px-0' : 'px-4'} py-3 rounded-xl transition-all active:scale-[0.98] font-label text-sm ${
                    isActive
                      ? 'text-primary font-bold bg-white/50 border-r-4 border-primary'
                      : 'text-[#757c7b] hover:bg-white/30'
                  }`
                }
              >
                <Icon size={20} className="shrink-0" />
                {!collapsed && <span className="truncate">{label}</span>}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 w-6 h-6 bg-white border border-outline-variant rounded-full flex items-center justify-center shadow-md z-[60] hover:bg-primary hover:text-white transition-all active:scale-90"
        >
          <ChevronLeft size={12} className={collapsed ? 'rotate-180' : ''} />
        </button>

        {/* Footer */}
        <div className="mt-auto p-4 space-y-2">
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-label text-sm ${
                isActive ? 'text-primary font-bold bg-white/50' : 'text-[#757c7b] hover:bg-white/50'
              }`
            }
          >
            <Settings size={20} className="shrink-0" />
            {!collapsed && <span>Settings</span>}
          </NavLink>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[#757c7b] hover:bg-white/50 transition-all font-label text-sm"
          >
            <LogOut size={20} className="shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>

          {/* User Profile */}
          <div className={`p-4 bg-white/40 rounded-2xl flex items-center gap-3 cursor-pointer hover:bg-white/60 transition-colors ${collapsed ? 'justify-center' : ''}`}>
            <img
              alt="User"
              className="w-8 h-8 rounded-full bg-surface shrink-0"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCbF0UQcYqIXP6UJ0Z7etWRkvhl0-Qfg_UpajQQzO5uCGVaiS-gwUxhe9PtTsehr6PUxvt87OrP4tP41f_m8UBv5oXUo8w2rjgW1qhBBkFCjH2MJHuellDJ8-Dp85YjUmTg4o9EK1ycKPrBhv62RlHQreFp7IKgipWC2bjbjPL70ea7eGy389msN-P6rkgGwZhHZnMxBRIoXiinYKPytNm_h_4_IrSP1r1N3Cgc_zBrVOA7L5kHn74FVZ8NQGJwg6SCVP9CgQ9RupE"
            />
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold truncate">Executive Profile</p>
                <p className="text-[10px] text-outline">Executive Tier</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative bg-background overflow-hidden">
        {/* Top Bar */}
        <header className="w-full z-40 bg-background/80 backdrop-blur-md flex justify-between items-center h-16 px-6 shrink-0 border-b border-surface-container-high">
          {/* Agent Pills */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-2">
            {agents.slice(0, 5).map((agent) => (
              <button
                key={agent.id}
                onClick={() => setActiveAgent(activeAgent === agent.id ? null : agent.id)}
                className={`rounded-full px-4 py-1.5 flex items-center gap-2 font-headline text-xs font-medium whitespace-nowrap transition-all active:scale-95 ${
                  activeAgent === agent.id
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-surface text-[#757c7b] hover:bg-outline-variant/30'
                }`}
              >
                <Star size={14} />
                {agent.name}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-outline hover:text-primary transition-colors active:scale-90">
              <Search size={20} />
            </button>
            <button className="p-2 text-outline hover:text-primary transition-colors active:scale-90">
              <Bell size={20} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
