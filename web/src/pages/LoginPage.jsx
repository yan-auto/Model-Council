import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, Shield } from 'lucide-react';
import { listProviders } from '../api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Already logged in → go to chat or setup
    if (sessionStorage.getItem('council_logged_in') === 'true') {
      navigate('/chat', { replace: true });
    }
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    try {
      const data = await listProviders();
      const hasProviders = data.providers && data.providers.length > 0;
      sessionStorage.setItem('council_logged_in', 'true');
      navigate(hasProviders ? '/chat' : '/setup', { replace: true });
    } catch {
      // If API fails, go to setup
      sessionStorage.setItem('council_logged_in', 'true');
      navigate('/setup', { replace: true });
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
      {/* Background blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute -top-[10%] -left-[5%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute top-[60%] -right-[5%] w-[35%] h-[35%] rounded-full bg-[#59605f]/5 blur-[100px]" />
      </div>

      <main className="w-full max-w-[460px] flex flex-col gap-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center text-white">
            <Shield size={24} />
          </div>
          <div className="flex flex-col gap-1">
            <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">Council</h1>
            <p className="text-outline text-sm uppercase tracking-wide font-label">Privacy First AI Infrastructure</p>
          </div>
        </div>

        {/* Login Card */}
        <div className="bg-white/92 backdrop-blur-md border border-outline-variant/15 p-10 rounded-lg shadow-[0_20px_40px_rgba(45,52,51,0.06)]">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h2 className="font-headline text-xl font-semibold">Welcome back</h2>
              <p className="text-outline text-sm">Enter your credentials to access your secure workspace.</p>
            </div>

            {/* Social Login */}
            <div className="grid grid-cols-2 gap-3">
              <button disabled className="flex items-center justify-center gap-3 px-4 py-3 bg-surface-container-low opacity-50 rounded-full border border-outline-variant/20 font-label text-sm font-medium cursor-not-allowed">
                <img src="https://www.google.com/favicon.ico" className="w-5 h-5" alt="Google" />
                Google
              </button>
              <button disabled className="flex items-center justify-center gap-3 px-4 py-3 bg-surface-container-low opacity-50 rounded-full border border-outline-variant/20 font-label text-sm font-medium cursor-not-allowed">
                <img src="https://github.com/favicon.ico" className="w-5 h-5" alt="GitHub" />
                GitHub
              </button>
            </div>

            {/* Divider */}
            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-outline-variant/20" />
              <span className="flex-shrink mx-4 text-xs text-[#727784] uppercase tracking-widest font-label">or local account</span>
              <div className="flex-grow border-t border-outline-variant/20" />
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label text-xs font-semibold text-outline ml-1" htmlFor="email">WORK EMAIL</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all placeholder:text-outline/50"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center ml-1">
                  <label className="font-label text-xs font-semibold text-outline" htmlFor="password">PASSPHRASE</label>
                  <a className="font-label text-[10px] text-primary hover:underline font-bold" href="#">RECOVER</a>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPw ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-surface-container-low border border-outline-variant/20 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all placeholder:text-outline/50 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-outline hover:text-on-surface transition-colors"
                  >
                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 bg-gradient-to-r from-[#004496] to-primary text-white font-body font-semibold py-4 rounded-full shadow-lg hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign In to Council'}
              </button>
            </form>

            {/* Security Badge */}
            <div className="flex items-center justify-center gap-2 px-4 py-2 bg-[#dde4e2]/30 rounded-lg">
              <Lock size={14} className="text-outline" />
              <span className="font-label text-[11px] font-medium text-[#5f6665] uppercase tracking-wide">Local Encryption Active</span>
            </div>
          </div>
        </div>

        {/* Footer Links */}
        <div className="flex flex-col items-center gap-6">
          <p className="text-outline text-sm">
            Don't have an account?{' '}
            <a className="text-primary font-semibold hover:underline" href="#">Request Access</a>
          </p>
          <div className="flex gap-6 text-[11px] font-label font-bold text-[#727784] uppercase tracking-tighter">
            <a className="hover:text-outline transition-colors" href="/security">Security Policy</a>
            <a className="hover:text-outline transition-colors" href="/profile">Profile</a>
            <a className="hover:text-outline transition-colors" href="/providers">Infrastructure</a>
          </div>
        </div>
      </main>
    </div>
  );
}
