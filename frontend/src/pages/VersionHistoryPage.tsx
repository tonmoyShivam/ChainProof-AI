import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { api } from '@/services/api';

export function VersionHistoryPage() {
  const { modelId = '' } = useParams();
  const history = useQuery({
    queryKey: ['model-history', modelId],
    queryFn: () => api.modelHistory(modelId),
    enabled: Boolean(modelId),
  });
  const detail = useQuery({
    queryKey: ['model', modelId],
    queryFn: () => api.getModel(modelId),
    enabled: Boolean(modelId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Version history</h1>
          <p className="mt-1 text-sm text-slate-400">
            {detail.data?.name ?? modelId} — prior fingerprints are preserved.
          </p>
        </div>
        <Link to={`/models/${encodeURIComponent(modelId)}`}>
          <Button variant="outline">Back to details</Button>
        </Link>
      </div>

      {history.isLoading && <p className="text-sm text-slate-400">Loading history…</p>}
      {history.isError && <Alert variant="error">Could not load version history.</Alert>}
      {history.data && history.data.length === 0 && (
        <Card>
          <CardTitle>No versions</CardTitle>
          <CardDescription>This model family has no recorded versions yet.</CardDescription>
        </Card>
      )}

      <ol className="space-y-3">
        {history.data?.map((version) => (
          <li key={version.id}>
            <Card>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle>Version {version.version_number}</CardTitle>
                <Badge variant={version.registration_status === 'confirmed' ? 'ok' : 'pending'}>
                  {version.registration_status}
                </Badge>
              </div>
              <dl className="mt-3 grid gap-2 text-sm md:grid-cols-2">
                <div>
                  <dt className="text-slate-500">On-chain ID</dt>
                  <dd className="break-all font-mono text-xs">{version.on_chain_model_id}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Parent version row</dt>
                  <dd className="font-mono text-xs">{version.parent_version_id ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">SHA-256</dt>
                  <dd className="break-all font-mono text-xs">{version.sha256_hash}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Transaction</dt>
                  <dd className="break-all font-mono text-xs">{version.transaction_hash}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Registered</dt>
                  <dd>{new Date(version.registered_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Framework</dt>
                  <dd>
                    {version.framework || '—'} {version.framework_version}
                  </dd>
                </div>
              </dl>
              <div className="mt-3">
                <Link
                  to={`/verify?model_id=${encodeURIComponent(version.on_chain_model_id)}`}
                  className="text-sm text-accent-muted hover:underline"
                >
                  Verify this version
                </Link>
              </div>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}
