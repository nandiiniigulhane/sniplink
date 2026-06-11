import { useState, useEffect, useRef, useCallback, type FormEvent, type KeyboardEvent } from 'react';
import { shortenUrl, login, register } from './api';

type Tab = 'shorten' | 'login' | 'register';
type Status = 'idle' | 'loading' | 'success' | 'error';

function useAnnounce() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!message) return;
    const timeout = setTimeout(() => setMessage(''), 100);
    return () => clearTimeout(timeout);
  }, [message]);

  return { announcement: message, announce: setMessage };
}

function App() {
  const [tab, setTab] = useState<Tab>('shorten');
  const [user, setUser] = useState<{ email: string } | null>(null);
  const { announcement, announce } = useAnnounce();
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as 'dark' | 'light') || 'dark';
    }
    return 'dark';
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    const email = localStorage.getItem('email');
    if (token && email) setUser({ email });
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      announce(`Switched to ${next} mode`);
      return next;
    });
  }, [announce]);

  const handleSignOut = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    setUser(null);
    setTab('shorten');
    announce('Signed out');
  }, [announce]);

  return (
    <>
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      <button
        onClick={toggleTheme}
        className="theme-toggle"
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>

      <main id="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', paddingBottom: 60 }}>
        <div style={{
          maxWidth: 560,
          width: '100%',
          margin: '0 auto',
          padding: '60px 24px 0',
          animation: 'fadeInUp 0.5s ease-out',
        }}>
          <header style={{ textAlign: 'center', marginBottom: 40 }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 52,
              height: 52,
              borderRadius: 16,
              background: 'linear-gradient(135deg, var(--primary), #8b5cf6)',
              marginBottom: 20,
              boxShadow: 'var(--shadow-glow)',
            }} aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
            </div>
            <h1 style={{
              fontSize: 36,
              fontWeight: 800,
              letterSpacing: '-0.8px',
              lineHeight: 1.15,
              marginBottom: 10,
              background: 'linear-gradient(135deg, var(--text), var(--text-secondary))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              URL Shortner
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 16, lineHeight: 1.5, maxWidth: 380, margin: '0 auto' }}>
              Shorten, share, and track your links with custom aliases and expiration dates.
            </p>
          </header>

          {user && (
            <section
              aria-label="Account status"
              style={{
                background: 'var(--surface-glass)',
                backdropFilter: 'blur(20px)',
                borderRadius: 'var(--radius)',
                padding: '14px 18px',
                marginBottom: 24,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                border: '1px solid var(--border)',
                animation: 'fadeIn 0.3s ease-out',
                boxShadow: '0 4px 24px -8px var(--shadow-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--primary), #8b5cf6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 14,
                  fontWeight: 700,
                  color: '#fff',
                }} aria-hidden="true">
                  {user.email[0].toUpperCase()}
                </div>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                  <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{user.email}</strong>
                </span>
              </div>
              <button
                onClick={handleSignOut}
                aria-label="Sign out of your account"
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  padding: '6px 16px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 500,
                  transition: 'all var(--transition-fast)',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--danger)'; e.currentTarget.style.color = 'var(--danger)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
              >
                Sign out
              </button>
            </section>
          )}

          {!user && (
            <nav
              aria-label="Navigation tabs"
              role="tablist"
              style={{
                display: 'flex',
                gap: 4,
                marginBottom: 28,
                background: 'var(--surface)',
                borderRadius: 'var(--radius)',
                padding: 4,
                border: '1px solid var(--border)',
              }}
            >
              {(['shorten', 'login', 'register'] as Tab[]).map((t) => (
                <button
                  key={t}
                  role="tab"
                  aria-selected={tab === t}
                  aria-controls={`panel-${t}`}
                  id={`tab-${t}`}
                  onClick={() => setTab(t)}
                  onKeyDown={(e: KeyboardEvent) => {
                    const tabs: Tab[] = ['shorten', 'login', 'register'];
                    const idx = tabs.indexOf(t);
                    if (e.key === 'ArrowRight') { setTab(tabs[(idx + 1) % 3]); }
                    if (e.key === 'ArrowLeft') { setTab(tabs[(idx + 2) % 3]); }
                  }}
                  style={{
                    flex: 1,
                    padding: '11px 0',
                    borderRadius: 10,
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: 14,
                    fontWeight: 600,
                    background: tab === t ? 'var(--primary)' : 'transparent',
                    color: tab === t ? '#fff' : 'var(--text-muted)',
                    transition: 'all var(--transition-base)',
                    position: 'relative',
                  }}
                >
                  {t === 'shorten' ? 'Shorten' : t === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </nav>
          )}

          {(!user || tab === 'shorten') && (
            <section id="panel-shorten" role="tabpanel" aria-labelledby="tab-shorten">
              <ShortenForm onSuccess={() => announce('URL shortened successfully')} />
            </section>
          )}
          {!user && tab === 'login' && (
            <section id="panel-login" role="tabpanel" aria-labelledby="tab-login">
              <LoginForm onLogin={setUser} announce={announce} />
            </section>
          )}
          {!user && tab === 'register' && (
            <section id="panel-register" role="tabpanel" aria-labelledby="tab-register">
              <RegisterForm onLogin={setUser} announce={announce} />
            </section>
          )}
        </div>
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '24px',
        color: 'var(--text-muted)',
        fontSize: 13,
        borderTop: '1px solid var(--border)',
        background: 'var(--surface)',
      }}>
        <span>URL Shortner</span>
        <span style={{ margin: '0 8px', color: 'var(--border)' }}>·</span>
        <span>Free &amp; open source</span>
      </footer>
    </>
  );
}

function ShortenForm({ onSuccess }: { onSuccess: () => void }) {
  const [longUrl, setLongUrl] = useState('');
  const [customAlias, setCustomAlias] = useState('');
  const [expiresInDays, setExpiresInDays] = useState('');
  const [password, setPassword] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<{ short_url: string; alias: string; expires_at: string | null; has_password: boolean } | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [hasShake, setHasShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (status === 'error' && error) {
      setHasShake(true);
      const t = setTimeout(() => setHasShake(false), 500);
      return () => clearTimeout(t);
    }
  }, [status, error]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!longUrl.trim()) return;

    setStatus('loading');
    setError('');
    setResult(null);

    try {
      const data = await shortenUrl(
        longUrl,
        customAlias.trim() || undefined,
        expiresInDays ? Number(expiresInDays) : undefined,
        password.trim() || undefined,
      );
      setResult(data);
      setStatus('success');
      setLongUrl('');
      setCustomAlias('');
      setExpiresInDays('');
      onSuccess();
      inputRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to shorten URL');
      setStatus('error');
    }
  };

  const handleCopy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.short_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        animation: 'fadeInUp 0.4s ease-out',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <label
          htmlFor="long-url"
          style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}
        >
          Long URL
        </label>
        <div style={{ position: 'relative' }}>
          <input
            ref={inputRef}
            id="long-url"
            type="url"
            value={longUrl}
            onChange={(e) => { setLongUrl(e.target.value); if (error) setError(''); }}
            placeholder="https://example.com/very-long-url..."
            required
            aria-required="true"
            aria-invalid={!!error}
            aria-describedby={error ? 'shorten-error' : undefined}
            autoComplete="url"
            style={{
              width: '100%',
              padding: '16px 16px 16px 44px',
              borderRadius: 'var(--radius)',
              background: 'var(--surface)',
              border: `1.5px solid ${error ? 'var(--danger)' : 'var(--border)'}`,
              color: 'var(--text)',
              fontSize: 15,
              outline: 'none',
              transition: 'all var(--transition-fast)',
              boxShadow: error ? '0 0 0 4px var(--danger-glow)' : 'none',
            }}
            onFocus={e => { if (!error) e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 0 0 4px var(--primary-glow)'; }}
            onBlur={e => { if (!error) e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
          />
          <svg
            aria-hidden="true"
            width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
          >
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
          </svg>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        aria-expanded={showAdvanced}
        aria-controls="advanced-options"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 0',
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          fontSize: 13,
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'color var(--transition-fast)',
        }}
        onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; }}
      >
        <svg
          aria-hidden="true"
          width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round"
          style={{ transform: showAdvanced ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform var(--transition-fast)' }}
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
        Advanced options
      </button>

      {showAdvanced && (
        <div
          id="advanced-options"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 12,
            animation: 'fadeIn 0.2s ease-out',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label
              htmlFor="custom-alias"
              style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}
            >
              Custom alias
            </label>
            <input
              id="custom-alias"
              type="text"
              value={customAlias}
              onChange={(e) => setCustomAlias(e.target.value)}
              placeholder="my-link"
              minLength={4}
              maxLength={20}
              pattern="[a-zA-Z0-9_-]+"
              autoComplete="off"
              aria-label="Custom alias for your short URL, 4 to 20 characters"
              style={{
                padding: '14px 16px',
                borderRadius: 'var(--radius)',
                background: 'var(--surface)',
                border: '1.5px solid var(--border)',
                color: 'var(--text)',
                fontSize: 15,
                outline: 'none',
                transition: 'all var(--transition-fast)',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 0 0 4px var(--primary-glow)'; }}
              onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label
              htmlFor="expiry-days"
              style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}
            >
              Expires in (days)
            </label>
            <input
              id="expiry-days"
              type="number"
              value={expiresInDays}
              onChange={(e) => setExpiresInDays(e.target.value)}
              placeholder="30"
              min={1}
              max={365}
              aria-label="Number of days until the URL expires, 1 to 365"
              style={{
                padding: '14px 16px',
                borderRadius: 'var(--radius)',
                background: 'var(--surface)',
                border: '1.5px solid var(--border)',
                color: 'var(--text)',
                fontSize: 15,
                outline: 'none',
                transition: 'all var(--transition-fast)',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 0 0 4px var(--primary-glow)'; }}
              onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label
              htmlFor="url-password"
              style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}
            >
              Password
            </label>
            <input
              id="url-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Protect URL"
              minLength={4}
              autoComplete="new-password"
              aria-label="Password to protect this URL, minimum 4 characters"
              style={{
                padding: '14px 16px',
                borderRadius: 'var(--radius)',
                background: 'var(--surface)',
                border: '1.5px solid var(--border)',
                color: 'var(--text)',
                fontSize: 15,
                outline: 'none',
                transition: 'all var(--transition-fast)',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 0 0 4px var(--primary-glow)'; }}
              onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
            />
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={status === 'loading'}
        aria-busy={status === 'loading'}
        style={{
          position: 'relative',
          padding: '16px 0',
          borderRadius: 'var(--radius)',
          background: status === 'loading'
            ? 'var(--primary-hover)'
            : 'linear-gradient(135deg, var(--primary), #6366f1)',
          border: 'none',
          color: '#fff',
          fontSize: 16,
          fontWeight: 700,
          cursor: status === 'loading' ? 'wait' : 'pointer',
          opacity: status === 'loading' ? 0.85 : 1,
          transition: 'all var(--transition-base)',
          overflow: 'hidden',
          boxShadow: status === 'loading' ? 'none' : '0 4px 20px -4px var(--primary-glow)',
        }}
        onMouseEnter={e => { if (status !== 'loading') e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 8px 28px -4px var(--primary-glow)'; }}
        onMouseLeave={e => { if (status !== 'loading') e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 20px -4px var(--primary-glow)'; }}
      >
        {status === 'loading' ? (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              display: 'inline-block',
              width: 18,
              height: 18,
              border: '2.5px solid rgba(255,255,255,0.3)',
              borderTopColor: '#fff',
              borderRadius: '50%',
              animation: 'spin 0.7s linear infinite',
            }} aria-hidden="true" />
            Shortening...
          </span>
        ) : (
          'Shorten URL'
        )}
      </button>

      {error && (
        <div
          id="shorten-error"
          role="alert"
          style={{
            padding: '14px 18px',
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: 'var(--radius)',
            color: 'var(--danger)',
            fontSize: 14,
            fontWeight: 500,
            animation: hasShake ? 'shake 0.4s ease-out' : 'fadeIn 0.3s ease-out',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}

      {result && (
        <article
          aria-label="Shortened URL result"
          style={{
            padding: 20,
            background: 'rgba(34,197,94,0.06)',
            border: '1px solid rgba(34,197,94,0.2)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            animation: 'scaleIn 0.35s ease-out',
            boxShadow: '0 0 30px -8px var(--success-glow)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 14,
              color: 'var(--success)',
              fontWeight: 700,
            }}>
              <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Link shortened!
              {result.has_password && (
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  marginLeft: 4,
                  padding: '2px 8px',
                  borderRadius: 6,
                  background: 'rgba(245,158,11,0.15)',
                  color: 'var(--warning)',
                  fontSize: 11,
                  fontWeight: 600,
                }}>
                  <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  Password protected
                </span>
              )}
            </span>
            {result.expires_at && (
              <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500 }}>
                Expires {new Date(result.expires_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            )}
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '14px 16px',
            background: 'var(--surface-glass)',
            backdropFilter: 'blur(20px)',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border)',
          }}>
            <a
              href={result.short_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open shortened URL: ${result.short_url}`}
              style={{
                color: 'var(--primary)',
                textDecoration: 'none',
                fontSize: 15,
                fontWeight: 600,
                flex: 1,
                wordBreak: 'break-all',
                transition: 'color var(--transition-fast)',
              }}
            >
              {result.short_url}
            </a>
            <button
              onClick={handleCopy}
              aria-label={copied ? 'URL copied to clipboard' : 'Copy shortened URL to clipboard'}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                borderRadius: 'var(--radius-sm)',
                background: copied ? 'linear-gradient(135deg, var(--success), #16a34a)' : 'var(--surface-raised)',
                border: copied ? 'none' : '1px solid var(--border)',
                color: copied ? '#fff' : 'var(--text-secondary)',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all var(--transition-fast)',
              }}
            >
              {copied ? (
                <>
                  <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Copied
                </>
              ) : (
                <>
                  <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                  Copy
                </>
              )}
            </button>
          </div>
        </article>
      )}
    </form>
  );
}

function LoginForm({ onLogin, announce }: { onLogin: (u: { email: string }) => void; announce: (m: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const data = await login(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('email', data.email);
      onLogin({ email: data.email });
      announce('Signed in successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeInUp 0.4s ease-out' }}>
      <InputField id="login-email" label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" autoComplete="email" />
      <InputField id="login-password" label="Password" type="password" value={password} onChange={setPassword} placeholder="Enter your password" autoComplete="current-password" />
      {error && <ErrorBox id="login-error">{error}</ErrorBox>}
      <SubmitButton loading={status === 'loading'} ariaLabel="Sign in to your account">Sign In</SubmitButton>
    </form>
  );
}

function RegisterForm({ onLogin, announce }: { onLogin: (u: { email: string }) => void; announce: (m: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const data = await register(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('email', data.email);
      onLogin({ email: data.email });
      announce('Account created and signed in');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeInUp 0.4s ease-out' }}>
      <InputField id="register-email" label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" autoComplete="email" />
      <InputField id="register-password" label="Password" type="password" value={password} onChange={setPassword} placeholder="At least 8 characters" autoComplete="new-password" />
      {error && <ErrorBox id="register-error">{error}</ErrorBox>}
      <SubmitButton loading={status === 'loading'} ariaLabel="Create a new account">Create Account</SubmitButton>
    </form>
  );
}

function InputField({ id, label, type, value, onChange, placeholder, autoComplete }: {
  id: string;
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  autoComplete: string;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label
        htmlFor={id}
        style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        autoComplete={autoComplete}
        style={{
          padding: '14px 16px',
          borderRadius: 'var(--radius)',
          background: 'var(--surface)',
          border: '1.5px solid var(--border)',
          color: 'var(--text)',
          fontSize: 15,
          outline: 'none',
          transition: 'all var(--transition-fast)',
        }}
        onFocus={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 0 0 4px var(--primary-glow)'; }}
        onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
      />
    </div>
  );
}

function SubmitButton({ loading, children, ariaLabel }: { loading: boolean; children: React.ReactNode; ariaLabel: string }) {
  return (
    <button
      type="submit"
      disabled={loading}
      aria-label={ariaLabel}
      aria-busy={loading}
      style={{
        position: 'relative',
        padding: '16px 0',
        borderRadius: 'var(--radius)',
        background: loading
          ? 'var(--primary-hover)'
          : 'linear-gradient(135deg, var(--primary), #6366f1)',
        border: 'none',
        color: '#fff',
        fontSize: 16,
        fontWeight: 700,
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.85 : 1,
        transition: 'all var(--transition-base)',
        boxShadow: loading ? 'none' : '0 4px 20px -4px var(--primary-glow)',
      }}
      onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 8px 28px -4px var(--primary-glow)'; }}
      onMouseLeave={e => { if (!loading) e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 20px -4px var(--primary-glow)'; }}
    >
      {loading ? (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            display: 'inline-block',
            width: 18,
            height: 18,
            border: '2.5px solid rgba(255,255,255,0.3)',
            borderTopColor: '#fff',
            borderRadius: '50%',
            animation: 'spin 0.7s linear infinite',
          }} aria-hidden="true" />
          Please wait...
        </span>
      ) : children}
    </button>
  );
}

function ErrorBox({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <div
      id={id}
      role="alert"
      style={{
        padding: '14px 18px',
        background: 'rgba(239,68,68,0.08)',
        border: '1px solid rgba(239,68,68,0.25)',
        borderRadius: 'var(--radius)',
        color: 'var(--danger)',
        fontSize: 14,
        fontWeight: 500,
        animation: 'shake 0.4s ease-out, fadeIn 0.3s ease-out',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}
    >
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      {children}
    </div>
  );
}

export default App;
