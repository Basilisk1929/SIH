import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('investigator.demo@cybershield.local');
  const [password, setPassword] = useState('InvestigatorDemo@2024!');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  // If already authenticated, redirect
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide officer email and password.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await login(username, password, rememberMe);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickDemoLogin = async (role: UserRole) => {
    let email = '';
    let pwd = '';
    switch (role) {
      case 'INVESTIGATOR':
        email = 'investigator.demo@cybershield.local';
        pwd = 'InvestigatorDemo@2024!';
        break;
      case 'SUPERVISOR':
        email = 'supervisor.demo@cybershield.local';
        pwd = 'SupervisorDemo@2024!';
        break;
      case 'ANALYST':
        email = 'analyst.demo@cybershield.local';
        pwd = 'AnalystDemo@2024!';
        break;
      case 'ADMIN':
        email = 'admin.demo@cybershield.local';
        pwd = 'AdminDemo@2024!';
        break;
    }
    setUsername(email);
    setPassword(pwd);
    setSubmitting(true);
    setError(null);
    try {
      await login(email, pwd, true);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#070a12',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        backgroundImage: 'radial-gradient(ellipse at 50% 20%, rgba(0, 242, 254, 0.08), transparent 70%)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: '#0d1322',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '36px 32px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        }}
      >
        {/* Brand header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #00f2fe, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              margin: '0 auto 14px auto',
              boxShadow: '0 0 20px rgba(0, 242, 254, 0.3)',
            }}
          >
            ⚡
          </div>
          <h2 style={{ fontSize: '1.4rem', color: '#f8fafc', fontWeight: 700, margin: 0, letterSpacing: '-0.02em' }}>
            CyberShield-Intel
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '6px 0 0 0' }}>
            Financial Cybercrime Intelligence & Mule Network Triage
          </p>
        </div>

        {/* Evaluation Banner */}
        <div
          style={{
            backgroundColor: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            borderRadius: '8px',
            padding: '12px 14px',
            fontSize: '0.74rem',
            color: '#c7d2fe',
            marginBottom: '20px',
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 700, letterSpacing: '0.04em', color: '#a5b4fc', marginBottom: '4px' }}>
            SMART INDIA HACKATHON — EVALUATION MODE
          </div>
          <div>Public SIH demonstration environment — synthetic data only.</div>
        </div>

        {/* Quick Demo Access */}
        <div style={{ marginBottom: '22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Quick Demo Access
            </label>
            <span style={{ fontSize: '0.65rem', color: '#64748b' }}>One-Click Judge Login</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {(['INVESTIGATOR', 'SUPERVISOR', 'ANALYST', 'ADMIN'] as UserRole[]).map((r) => (
              <button
                key={r}
                type="button"
                disabled={submitting}
                onClick={() => handleQuickDemoLogin(r)}
                style={{
                  backgroundColor: '#121a2d',
                  border: '1px solid #334155',
                  color: '#38bdf8',
                  borderRadius: '6px',
                  padding: '8px 4px',
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  textAlign: 'center',
                }}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#fca5a5',
              padding: '10px 14px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              marginBottom: '20px',
            }}
          >
            {error}
          </div>
        )}

        {/* Login form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontSize: '0.8rem', color: '#cbd5e1', display: 'block', marginBottom: '6px', fontWeight: 500 }}>
              Officer Official Email / Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="officer@cybercell.gov.in"
              required
              style={{
                width: '100%',
                backgroundColor: '#121a2d',
                border: '1px solid #334155',
                color: '#f8fafc',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '0.875rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ fontSize: '0.8rem', color: '#cbd5e1', display: 'block', marginBottom: '6px', fontWeight: 500 }}>
              Cryptographic Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                backgroundColor: '#121a2d',
                border: '1px solid #334155',
                color: '#f8fafc',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '0.875rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', fontSize: '0.8rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ accentColor: '#00f2fe' }}
              />
              Persist session in browser
            </label>
            <span style={{ color: '#64748b' }}>v0.1.0 SIH</span>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%',
              backgroundColor: '#00f2fe',
              color: '#070a12',
              border: 'none',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '0.95rem',
              fontWeight: 700,
              cursor: submitting ? 'not-allowed' : 'pointer',
              letterSpacing: '0.02em',
              boxShadow: '0 0 20px rgba(0, 242, 254, 0.3)',
              transition: 'opacity 0.15s ease',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            {submitting ? 'Authenticating Officer...' : 'Authorize Secure Access'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.72rem', color: '#64748b' }}>
          Restricted Law Enforcement Intelligence System • Authorized Personnel Only
        </div>
      </div>
    </div>
  );
};
