import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { MainLayout } from './layouts/MainLayout';

// Pages
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Alerts } from './pages/Alerts';
import { AlertDetail } from './pages/AlertDetail';
import { Cases } from './pages/Cases';
import { CaseDetail } from './pages/CaseDetail';
import { Transactions } from './pages/Transactions';
import { AccountDetail } from './pages/AccountDetail';
import { Complaints } from './pages/Complaints';
import { Graph } from './pages/Graph';
import { Map } from './pages/Map';

// Global styles
import './styles/theme.css';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Law Enforcement Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/alerts/:id" element={<AlertDetail />} />
              <Route path="/cases" element={<Cases />} />
              <Route path="/cases/:id" element={<CaseDetail />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/accounts/:id" element={<AccountDetail />} />
              <Route path="/complaints" element={<Complaints />} />
              <Route path="/graph" element={<Graph />} />
              <Route path="/map" element={<Map />} />
            </Route>
          </Route>

          {/* Fallback to Dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
