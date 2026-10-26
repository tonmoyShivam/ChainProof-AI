import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError, api } from '@/services/api';
import type { VerificationResult } from '@/types/api';
import { classifyVerification, verificationHeadline } from '@/utils/verification';

function statusVariant(status: VerificationResult['status']) {
  if (status === 'VERIFIED') return 'ok' as const;
  if (status === 'INTEGRITY_MISMATCH') return 'fail' as const;
  if (status === 'VERIFICATION_UNAVAILABLE') return 'pending' as const;
  return 'muted' as const;
}

function outcomeFromResult(result: VerificationResult) {
  const match =
    result.status === 'VERIFIED' ? true : result.status === 'INTEGRITY_MISMATCH' ? false : null;
  return classifyVerification({
    match,
    blockchainAvailable: result.status !== 'VERIFICATION_UNAVAILABLE',
    errorCode: result.status === 'MODEL_NOT_FOUND' ? result.status : null,
  });
}

export function VerifyModelPage() {
  const [params] = useSearchParams();
  const [modelId, setModelId] = useState(params.get('model_id') ?? '');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!modelId.trim()) throw new ApiError('Model ID is required', 400);
      if (!file) throw new ApiError('Choose a file to verify', 400);
      const body = new FormData();
      body.append('model_id', modelId.trim());
      body.append('file', file);
      return api.verifyModel(body);
    },
    onSuccess: (data) => {
      setResult(data);
      setError(null);
    },
    onError: (err) => {
      setResult(null);
      setError(err instanceof ApiError ? err.message : 'Verification failed');
    },
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Verify model</h1>
        <p className="mt-1 text-sm text-slate-400">
          Compare an uploaded artifact against the on-chain fingerprint.
        </p>
      </div>

      <Card>
        <CardTitle>Verification request</CardTitle>
        <CardDescription>Infrastructure failures are never reported as VERIFIED.</CardDescription>
        <form
          className="mt-4 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <div>
            <Label htmlFor="model_id">Model ID</Label>
            <Input
              id="model_id"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="0x…"
              disabled={mutation.isPending}
            />
          </div>
          <div>
            <Label htmlFor="file">Artifact file</Label>
            <Input
              id="file"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={mutation.isPending}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Progress:</span>
            {mutation.isPending ? (
              <Badge variant="pending">Hashing & querying chain…</Badge>
            ) : (
              <Badge variant="muted">Idle</Badge>
            )}
          </div>
          {error && <Alert variant="error">{error}</Alert>}
          <Button type="submit" disabled={mutation.isPending || !file || !modelId.trim()}>
            {mutation.isPending ? 'Verifying…' : 'Verify integrity'}
          </Button>
        </form>
      </Card>

      {result && (
        <Card>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>{verificationHeadline(outcomeFromResult(result))}</CardTitle>
            <Badge variant={statusVariant(result.status)}>{result.status}</Badge>
          </div>
          <p className="mt-2 text-sm text-slate-300">{result.detail}</p>
          <dl className="mt-4 space-y-2 font-mono text-xs text-slate-400">
            <div>
              <dt className="text-slate-500">Expected hash</dt>
              <dd className="break-all text-slate-200">{result.expected_hash ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Actual hash</dt>
              <dd className="break-all text-slate-200">{result.actual_hash ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Creator wallet</dt>
              <dd>{result.creator_wallet ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">On-chain version</dt>
              <dd>{result.on_chain_version ?? '—'}</dd>
            </div>
          </dl>
        </Card>
      )}
    </div>
  );
}
