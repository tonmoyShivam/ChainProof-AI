import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/services/api';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const chain = useQuery({
    queryKey: ['blockchain-health'],
    queryFn: api.blockchainHealth,
    retry: false,
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">Profile, wallet status, and session controls.</p>
      </div>

      <Card>
        <CardTitle>Profile</CardTitle>
        <dl className="mt-3 space-y-2 text-sm">
          <div>
            <dt className="text-slate-500">Display name</dt>
            <dd>{user?.display_name}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Email</dt>
            <dd>{user?.email}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Role</dt>
            <dd>
              <Badge>{user?.role}</Badge>
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">User ID</dt>
            <dd className="font-mono text-xs">{user?.id}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <CardTitle>Wallet connection</CardTitle>
        <CardDescription>
          MetaMask wallet auth is a secondary feature. Status below is a placeholder until wallet
          login is enabled.
        </CardDescription>
        <div className="mt-3 flex items-center gap-2">
          <Badge variant="muted">Not connected</Badge>
          <span className="text-sm text-slate-400">
            {user?.wallet_address ?? 'No wallet address on profile'}
          </span>
        </div>
        <Button className="mt-4" variant="outline" disabled>
          Connect MetaMask (coming later)
        </Button>
      </Card>

      <Card>
        <CardTitle>Infrastructure</CardTitle>
        {chain.isLoading && <p className="mt-2 text-sm text-slate-400">Checking blockchain…</p>}
        {chain.isError && <Alert variant="error">Could not reach blockchain health endpoint.</Alert>}
        {chain.data && (
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-slate-500">RPC</span>
              <Badge variant={chain.data.connected ? 'ok' : 'fail'}>
                {chain.data.connected ? 'Connected' : 'Unavailable'}
              </Badge>
            </div>
            <p className="text-slate-400">{chain.data.detail}</p>
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>Session</CardTitle>
        <Button
          className="mt-3"
          variant="danger"
          onClick={async () => {
            await logout();
            navigate('/login');
          }}
        >
          Log out
        </Button>
      </Card>
    </div>
  );
}
