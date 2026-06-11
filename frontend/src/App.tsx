import { useState, useEffect } from 'react';
import { shortenUrl, login, register } from './api';

type Tab = 'shorten' | 'login' | 'register';
type Status = 'idle' | 'loading' | 'success' | 'error';

function App() {
  const [tab, setTab] = useState<Tab>('shorten');
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const email = localStorage.getItem('email');
    if (token && email) setUser({ email });
  }, []);

  return (
    <div style={{
      maxWidth: 640,
      margin: '0 auto',
      padding: '60px 20px',
      width: '100%',
    }}>
      <header style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px', marginBottom: 8 }}>
          URL Shortner
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 15 }}>
          Paste a long URL, get a short one back.
        </p>
      </header>

      {user && (
        <div style={{
          background: 'var(--surface)',
          borderRadius: 'var(--radius)',
          padding: '12px 16px',
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          border: '1px solid var(--border)',
        }}>
          <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>
            Signed in as <strong style={{ color: 'var(--text)' }}>{user.email}</strong>
          </span>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('email');
              setUser(null);
            }}
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-muted)',
              padding: '6px 14px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            Sign out
          </button>
        </div>
      )}

      {!user && (
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'var(--surface)', borderRadius: 'var(--radius)', padding: 4, border: '1px solid var(--border)' }}>
          {(['shorten', 'login', 'register'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                flex: 1,
                padding: '10px 0',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 500,
                background: tab === t ? 'var(--primary)' : 'transparent',
                color: tab === t ? '#fff' : 'var(--text-muted)',
                transition: 'all 0.15s',
              }}
            >
              {t === 'shorten' ? 'Shorten' : t === 'login' ? 'Sign In' : 'Sign Up'}
            </button>
          ))}
        </div>
      )}

      {(!user || tab === 'shorten') && <ShortenForm />}
      {!user && tab === 'login' && <LoginForm onLogin={setUser} />}
      {!user && tab === 'register' && <RegisterForm onLogin={setUser} />}
    </div>
  );
}

function ShortenForm() {
  const [longUrl, setLongUrl] = useState('');
  const [customAlias, setCustomAlias] = useState('');
  const [expiresInDays, setExpiresInDays] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<{ short_url: string; alias: string; expires_at: string | null } | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
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
      );
      setResult(data);
      setStatus('success');
      setLongUrl('');
      setCustomAlias('');
      setExpiresInDays('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to shorten URL');
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-muted)' }}>Long URL</label>
        <input
          type="url"
          value={longUrl}
          onChange={(e) => setLongUrl(e.target.value)}
          placeholder="https://example.com/very-long-url..."
          required
          style={{
            width: '100%',
            padding: '14px 16px',
            borderRadius: 'var(--radius)',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
            fontSize: 15,
            outline: 'none',
            transition: 'border-color 0.15s',
          }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-muted)' }}>Custom alias (optional)</label>
          <input
            type="text"
            value={customAlias}
            onChange={(e) => setCustomAlias(e.target.value)}
            placeholder="my-link"
            minLength={4}
            maxLength={20}
            pattern="[a-zA-Z0-9_-]+"
            style={{
              padding: '14px 16px',
              borderRadius: 'var(--radius)',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              fontSize: 15,
              outline: 'none',
            }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-muted)' }}>Expires in (days)</label>
          <input
            type="number"
            value={expiresInDays}
            onChange={(e) => setExpiresInDays(e.target.value)}
            placeholder="30"
            min={1}
            max={365}
            style={{
              padding: '14px 16px',
              borderRadius: 'var(--radius)',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              fontSize: 15,
              outline: 'none',
            }}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={status === 'loading'}
        style={{
          padding: '14px 0',
          borderRadius: 'var(--radius)',
          background: status === 'loading' ? 'var(--primary-hover)' : 'var(--primary)',
          border: 'none',
          color: '#fff',
          fontSize: 15,
          fontWeight: 600,
          cursor: status === 'loading' ? 'wait' : 'pointer',
          opacity: status === 'loading' ? 0.8 : 1,
        }}
      >
        {status === 'loading' ? 'Shortening...' : 'Shorten URL'}
      </button>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius)', color: 'var(--danger)', fontSize: 14 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ padding: 20, background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 'var(--radius)', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, color: 'var(--success)', fontWeight: 600 }}>URL shortened!</span>
            {result.expires_at && (
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Expires {new Date(result.expires_at).toLocaleDateString()}
              </span>
            )}
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 16px',
            background: 'var(--surface)',
            borderRadius: 10,
            border: '1px solid var(--border)',
          }}>
            <a
              href={result.short_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: 15, fontWeight: 500, flex: 1, wordBreak: 'break-all' }}
            >
              {result.short_url}
            </a>
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.short_url);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                background: copied ? 'var(--success)' : 'var(--surface-hover)',
                border: 'none',
                color: copied ? '#fff' : 'var(--text)',
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      )}
    </form>
  );
}

function LoginForm({ onLogin }: { onLogin: (user: { email: string }) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const data = await login(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('email', data.email);
      onLogin({ email: data.email });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <InputField label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" />
      <InputField label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
      {error && <ErrorBox>{error}</ErrorBox>}
      <SubmitButton loading={status === 'loading'}>Sign In</SubmitButton>
    </form>
  );
}

function RegisterForm({ onLogin }: { onLogin: (user: { email: string }) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const data = await register(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('email', data.email);
      onLogin({ email: data.email });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <InputField label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" />
      <InputField label="Password" type="password" value={password} onChange={setPassword} placeholder="Min. 8 characters" />
      {error && <ErrorBox>{error}</ErrorBox>}
      <SubmitButton loading={status === 'loading'}>Create Account</SubmitButton>
    </form>
  );
}

function InputField({ label, type, value, onChange, placeholder }: {
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-muted)' }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        style={{
          padding: '14px 16px',
          borderRadius: 'var(--radius)',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          color: 'var(--text)',
          fontSize: 15,
          outline: 'none',
        }}
      />
    </div>
  );
}

function SubmitButton({ loading, children }: { loading: boolean; children: React.ReactNode }) {
  return (
    <button
      type="submit"
      disabled={loading}
      style={{
        padding: '14px 0',
        borderRadius: 'var(--radius)',
        background: loading ? 'var(--primary-hover)' : 'var(--primary)',
        border: 'none',
        color: '#fff',
        fontSize: 15,
        fontWeight: 600,
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.8 : 1,
      }}
    >
      {loading ? 'Please wait...' : children}
    </button>
  );
}

function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      padding: '12px 16px',
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.3)',
      borderRadius: 'var(--radius)',
      color: 'var(--danger)',
      fontSize: 14,
    }}>
      {children}
    </div>
  );
}

export default App;
