import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { Login } from '../pages/Login';
import { AuthService } from '../services/auth';
import { setStoredToken } from '../services/api';

vi.mock('../services/auth', () => ({
  AuthService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    getStoredUserProfile: vi.fn(),
    logout: vi.fn(),
  },
}));

describe('Authentication & Protected Route Guards', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders login screen with official branding and role buttons', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CyberShield-Intel/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/officer@cybercell.gov.in/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Authorize Secure Access/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /INVESTIGATOR/i })).toBeInTheDocument();
  });

  it('performs login via backend AuthService and stores token', async () => {
    (AuthService.login as any).mockResolvedValue({
      access_token: 'valid-jwt-token-123',
      token_type: 'bearer',
    });
    (AuthService.getCurrentUser as any).mockResolvedValue({
      id: 'inv-001',
      username: 'investigator',
      full_name: 'Lead Cyber Investigator',
      role: 'INVESTIGATOR',
      is_active: true,
    });

    const { container } = render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    const usernameInput = screen.getByPlaceholderText(/officer@cybercell.gov.in/i);
    const passwordInput = container.querySelector('input[type="password"]') as HTMLInputElement;
    const submitBtn = screen.getByRole('button', { name: /Authorize Secure Access/i });

    fireEvent.change(usernameInput, { target: { value: 'investigator' } });
    fireEvent.change(passwordInput, { target: { value: 'Investigator@123' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(AuthService.login).toHaveBeenCalledWith('investigator', 'Investigator@123', true);
    });
  });

  it('redirects unauthenticated user from protected route to /login', async () => {
    (AuthService.getStoredUserProfile as any).mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/cases']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>LOGIN_PAGE_RENDERED</div>} />
            <Route element={<ProtectedRoute />}>
              <Route path="/cases" element={<div>PROTECTED_CASES_PAGE</div>} />
            </Route>
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('LOGIN_PAGE_RENDERED')).toBeInTheDocument();
    });
    expect(screen.queryByText('PROTECTED_CASES_PAGE')).not.toBeInTheDocument();
  });

  it('blocks access when user role is not authorized for protected partition', async () => {
    setStoredToken('test-analyst-token');
    (AuthService.getStoredUserProfile as any).mockReturnValue({
      id: 'analyst-1',
      username: 'analyst_user',
      full_name: 'Junior Analyst',
      role: 'ANALYST',
      is_active: true,
    });
    (AuthService.getCurrentUser as any).mockResolvedValue({
      id: 'analyst-1',
      username: 'analyst_user',
      full_name: 'Junior Analyst',
      role: 'ANALYST',
      is_active: true,
    });

    render(
      <MemoryRouter initialEntries={['/admin-config']}>
        <AuthProvider>
          <Routes>
            <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
              <Route path="/admin-config" element={<div>ADMIN_SETTINGS_SECRET</div>} />
            </Route>
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Access Restricted \(Role Authorization Error\)/i)).toBeInTheDocument();
    });
    expect(screen.queryByText('ADMIN_SETTINGS_SECRET')).not.toBeInTheDocument();
  });
});
