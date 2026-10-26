import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { api } from '@/services/api';

function StatCard({ label, value, loading }: { label: string; value?: number; loading: boolean }) {
  return (
    <Card>
      <CardDescription>{label}</CardDescription>
      <p className="mt-2 font-mono text-3xl font-semibold text-white">
        {loading ? '…' : (value ?? 0)}
      </p>
    </Card>
  );
}

export function DashboardPage() {
  const stats = useQuery({ queryKey: ['dashboard-stats'], queryFn: api.dashboardStats });
  const activity = useQuery({ queryKey: ['recent-activity'], queryFn: api.recentActivity });
  const models = useQuery({ queryKey: ['models'], queryFn: api.listModels });

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-400">
            Live counts from the API — never hardcoded.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/register">
            <Button>Register model</Button>
          </Link>
          <Link to="/verify">
            <Button variant="outline">Verify model</Button>
          </Link>
        </div>
      </div>

      {stats.isError && <Alert variant="error">Failed to load dashboard stats.</Alert>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Registered models"
          value={stats.data?.total_registered_models}
          loading={stats.isLoading}
        />
        <StatCard
          label="Verification attempts"
          value={stats.data?.total_verification_attempts}
          loading={stats.isLoading}
        />
        <StatCard
          label="Successful verifications"
          value={stats.data?.successful_verifications}
          loading={stats.isLoading}
        />
        <StatCard
          label="Integrity mismatches"
          value={stats.data?.integrity_mismatches}
          loading={stats.isLoading}
        />
      </div>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-white">Recent registrations</h2>
        {activity.isLoading && <p className="text-sm text-slate-400">Loading activity…</p>}
        {activity.isError && <Alert variant="error">Could not load recent activity.</Alert>}
        {activity.data && activity.data.length === 0 && (
          <Card>
            <CardTitle>No registrations yet</CardTitle>
            <CardDescription>Register a model to see activity here.</CardDescription>
          </Card>
        )}
        {activity.data && activity.data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-navy-700">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-navy-900 text-slate-400">
                <tr>
                  <th className="px-3 py-2 font-medium">Model</th>
                  <th className="px-3 py-2 font-medium">Version</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Registered</th>
                </tr>
              </thead>
              <tbody>
                {activity.data.map((item) => (
                  <tr key={`${item.model_id}-${item.version}`} className="border-t border-navy-700">
                    <td className="px-3 py-2">
                      <Link
                        className="text-accent-muted hover:underline"
                        to={`/models/${encodeURIComponent(item.model_id)}`}
                      >
                        {item.name}
                      </Link>
                      <div className="font-mono text-xs text-slate-500">
                        {item.model_id.slice(0, 18)}…
                      </div>
                    </td>
                    <td className="px-3 py-2 font-mono">{item.version}</td>
                    <td className="px-3 py-2">
                      <Badge variant={item.status === 'confirmed' ? 'ok' : 'pending'}>
                        {item.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-slate-400">
                      {new Date(item.registration_time).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-white">Your models</h2>
        {models.isLoading && <p className="text-sm text-slate-400">Loading models…</p>}
        {models.data && models.data.length === 0 && (
          <p className="text-sm text-slate-400">No models in the registry yet.</p>
        )}
        <div className="grid gap-3 md:grid-cols-2">
          {models.data?.map((model) => (
            <Card key={model.model_id}>
              <CardTitle>{model.name}</CardTitle>
              <CardDescription>
                v{model.current_version} · {model.creator_wallet.slice(0, 10)}…
              </CardDescription>
              <div className="mt-3 flex gap-2">
                <Link to={`/models/${encodeURIComponent(model.model_id)}`}>
                  <Button size="sm" variant="secondary">
                    Details
                  </Button>
                </Link>
                <Link to={`/models/${encodeURIComponent(model.model_id)}/history`}>
                  <Button size="sm" variant="outline">
                    History
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
