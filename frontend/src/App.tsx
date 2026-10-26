import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AuthProvider } from '@/hooks/useAuth';
import { AppLayout } from '@/layouts/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { ModelDetailsPage } from '@/pages/ModelDetailsPage';
import { RegisterAccountPage } from '@/pages/RegisterAccountPage';
import { RegisterModelPage } from '@/pages/RegisterModelPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { VerifyModelPage } from '@/pages/VerifyModelPage';
import { VersionHistoryPage } from '@/pages/VersionHistoryPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register-account" element={<RegisterAccountPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/register" element={<RegisterModelPage />} />
                <Route path="/verify" element={<VerifyModelPage />} />
                <Route path="/models/:modelId" element={<ModelDetailsPage />} />
                <Route path="/models/:modelId/history" element={<VersionHistoryPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
