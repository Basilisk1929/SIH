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
  const [loadingMessage, setLoadingMessage] = useState<string>('Connecting to CyberShield backend...');

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

  const executeLogin = async (userEmail: string, userPwd: string, remember: boolean) => {
    setSubmitting(true);
    setError(null);
    setLoadingMessage('Connecting to CyberShield backend...');

    // If request takes longer than 6 seconds, backend may be waking up on Render free tier
    const wakeupTimer = setTimeout(() => {
      setLoadingMessage('Backend is waking up — this can take up to 30–60 seconds on the free-tier demo environment.');
    }, 6000);

    try {
      await login(userEmail, userPwd, remember);
      clearTimeout(wakeupTimer);
      navigate(from, { replace: true });
    } catch (err: any) {
      clearTimeout(wakeupTimer);
      const errMsg = err.message || '';
      if (errMsg.includes('Network Error') || errMsg.includes('Failed to fetch') || errMsg.includes('504') || errMsg.includes('502')) {
        setError('Backend is still waking up from Render free-tier sleep. Please wait a moment and click Authorize Secure Access again.');
      } else {
        setError(err.message || 'Authentication failed. Please verify credentials.');
      }
    } finally {
      clearTimeout(wakeupTimer);
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide officer email and password.');
      return;
    }
    await executeLogin(username, password, rememberMe);
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
    await executeLogin(email, pwd, true);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#000000',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: '#0a0a0a',
          border: '1px solid #202020',
          borderRadius: '12px',
          padding: '36px 32px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.8), 0 0 0 1px #161616',
        }}
      >
        {/* Official Brand Logo */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <img
            src="/cybershield-logo.png"
            alt="CyberShield Official Logo"
            style={{
              width: '160px',
              height: 'auto',
              maxHeight: '128px',
              margin: '0 auto 12px auto',
              display: 'block',
              objectFit: 'contain',
            }}
          />
          <h2 style={{ fontSize: '1.35rem', color: '#f5f5f5', fontWeight: 700, margin: 0, letterSpacing: '-0.02em' }}>
            CyberShield-Intel
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#a0a0a0', margin: '4px 0 0 0' }}>
            Financial Cybercrime Intelligence & Mule Network Triage
          </p>
        </div>

        {/* Evaluation Banner & Render Free-Tier Notice */}
        <div
          style={{
            backgroundColor: '#0f0f0f',
            border: '1px solid #262626',
            borderRadius: '8px',
            padding: '12px 14px',
            fontSize: '0.74rem',
            color: '#a0a0a0',
            marginBottom: '20px',
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 700, letterSpacing: '0.04em', color: '#f59e0b', marginBottom: '3px' }}>
            SMART INDIA HACKATHON — EVALUATION MODE
          </div>
          <div style={{ marginBottom: '6px' }}>Public demonstration environment — synthetic data only.</div>
          <div style={{ borderTop: '1px solid #1f1f1f', paddingTop: '6px', color: '#888888', fontSize: '0.71rem' }}>
            ⚡ <strong>Demo Environment Notice:</strong> The backend runs on Render's free tier and may take 30–60 seconds to wake up after inactivity. If login initially takes longer than usual, please wait a moment and try again.
          </div>
        </div>

        {/* Quick Demo Access */}
        <div style={{ marginBottom: '22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <label style={{ fontSize: '0.72rem', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Quick Demo Access
            </label>
            <span style={{ fontSize: '0.65rem', color: '#707070' }}>One-Click Judge Login</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {(['INVESTIGATOR', 'SUPERVISOR', 'ANALYST', 'ADMIN'] as UserRole[]).map((r) => (
              <button
                key={r}
                type="button"
                disabled={submitting}
                onClick={() => handleQuickDemoLogin(r)}
                style={{
                  backgroundColor: '#121212',
                  border: '1px solid #262626',
                  color: '#e5e5e5',
                  borderRadius: '6px',
                  padding: '8px 4px',
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s ease',
                }}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Loading status message */}
        {submitting && (
          <div
            style={{
              backgroundColor: '#121212',
              border: '1px solid #262626',
              borderRadius: '6px',
              padding: '10px 14px',
              marginBottom: '16px',
              fontSize: '0.78rem',
              color: '#38bdf8',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              lineHeight: 1.4,
            }}
          >
            <span style={{ fontSize: '1rem' }}>🔄</span>
            <span>{loadingMessage}</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#f87171',
              padding: '10px 14px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              marginBottom: '20px',
              lineHeight: 1.4,
            }}
          >
            {error}
          </div>
        )}

        {/* Login form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontSize: '0.8rem', color: '#a0a0a0', display: 'block', marginBottom: '6px', fontWeight: 500 }}>
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
                backgroundColor: '#050505',
                border: '1px solid #262626',
                color: '#f5f5f5',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '0.875rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ fontSize: '0.8rem', color: '#a0a0a0', display: 'block', marginBottom: '6px', fontWeight: 500 }}>
              Cryptographic Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                backgroundColor: '#050505',
                border: '1px solid #262626',
                color: '#f5f5f5',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '0.875rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', fontSize: '0.8rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a0a0a0', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ accentColor: '#0088ff' }}
              />
              Persist session in browser
            </label>
            <span style={{ color: '#707070' }}>v0.1.0 SIH</span>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%',
              backgroundColor: '#141414',
              color: '#f5f5f5',
              border: '1px solid #0088ff',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '0.95rem',
              fontWeight: 700,
              cursor: submitting ? 'not-allowed' : 'pointer',
              letterSpacing: '0.02em',
              boxShadow: '0 0 12px rgba(0, 136, 255, 0.15)',
              transition: 'all 0.15s ease',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            {submitting ? 'Connecting to CyberShield backend...' : 'Authorize Secure Access'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.72rem', color: '#707070' }}>
          Restricted Law Enforcement Intelligence System • Authorized Personnel Only
        </div>
      </div>
    </div>
  );
};
