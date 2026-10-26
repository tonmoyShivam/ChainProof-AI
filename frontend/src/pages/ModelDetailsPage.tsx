import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { api } from '@/services/api';

export function ModelDetailsPage() {
  const { modelId = '' } = useParams();
  const detail = useQuery({
    queryKey: ['model', modelId],
    queryFn: () => api.getModel(modelId),
    enabled: Boolean(modelId),
  });

  if (detail.isLoading) {
    return <p className="text-sm text-slate-400">Loading model details…</p>;
  }
  if (detail.isError) {
    return <Alert variant="error">Model not found or API error.</Alert>;
  }
  const model = detail.data;
  if (!model) return null;
  const latest = model.latest_version;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">{model.name}</h1>
          <p className="mt-1 text-sm text-slate-400">{model.description || 'No description'}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/verify?model_id=${encodeURIComponent(latest?.on_chain_model_id ?? model.model_id)}`}>
            <Button variant="outline">Verify</Button>
          </Link>
          <Link to={`/models/${encodeURIComponent(model.model_id)}/history`}>
            <Button variant="secondary">Version history</Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardTitle>Provenance metadata</CardTitle>
          <dl className="mt-3 space-y-2 text-sm">
            <div>
              <dt className="text-slate-500">Family model ID</dt>
              <dd className="break-all font-mono text-xs text-slate-200">{model.model_id}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Creator user</dt>
              <dd className="font-mono text-xs">{model.creator_user_id}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Creator wallet</dt>
              <dd className="font-mono text-xs">{model.creator_wallet}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Current version</dt>
              <dd>{model.current_version}</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <CardTitle>Latest on-chain record</CardTitle>
          {!latest && <CardDescription>No version rows available.</CardDescription>}
          {latest && (
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <dt className="text-slate-500">Status</dt>
                <Badge variant={latest.registration_status === 'confirmed' ? 'ok' : 'pending'}>
                  {latest.registration_status}
                </Badge>
              </div>
              <div>
                <dt className="text-slate-500">SHA-256</dt>
                <dd className="break-all font-mono text-xs text-slate-200">{latest.sha256_hash}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Tx hash</dt>
                <dd className="break-all font-mono text-xs">{latest.transaction_hash}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Contract / chain</dt>
                <dd className="font-mono text-xs">
                  {latest.contract_address} · {latest.chain_id}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Storage</dt>
                <dd className="font-mono text-xs">
                  {latest.storage_type}: {latest.storage_path}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Registered</dt>
                <dd>{new Date(latest.registered_at).toLocaleString()}</dd>
              </div>
            </dl>
          )}
        </Card>
      </div>
    </div>
  );
}
