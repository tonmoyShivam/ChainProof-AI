import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { z } from 'zod';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ApiError, api } from '@/services/api';
import type { ModelRegistration } from '@/types/api';

const schema = z.object({
  name: z.string().min(1, 'Model name is required'),
  description: z.string().optional(),
  version: z.string().min(1, 'Version is required'),
  framework: z.string().optional(),
  framework_version: z.string().optional(),
  architecture: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

type Phase = 'idle' | 'uploading' | 'hashing' | 'pending_tx' | 'success' | 'error';

export function RegisterModelPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModelRegistration | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { version: '1.0.0' },
  });

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (!file) throw new ApiError('Choose a model file to upload', 400);
      const body = new FormData();
      body.append('file', file);
      body.append('name', values.name);
      body.append('description', values.description ?? '');
      body.append('version', values.version);
      body.append('framework', values.framework ?? '');
      body.append('framework_version', values.framework_version ?? '');
      body.append('architecture', values.architecture ?? '');
      setPhase('uploading');
      setPhase('hashing');
      setPhase('pending_tx');
      return api.registerModel(body);
    },
    onSuccess: (data) => {
      setResult(data);
      setPhase('success');
      void queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      void queryClient.invalidateQueries({ queryKey: ['recent-activity'] });
      void queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (err) => {
      setPhase('error');
      setError(err instanceof ApiError ? err.message : 'Registration failed');
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    setError(null);
    setResult(null);
    mutation.mutate(values);
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Register model</h1>
        <p className="mt-1 text-sm text-slate-400">
          Upload an artifact. Success is shown only after blockchain confirmation.
        </p>
      </div>

      <Card>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div>
            <Label htmlFor="file">Model file</Label>
            <Input
              id="file"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={mutation.isPending}
            />
            {!file && form.formState.isSubmitted && (
              <p className="mt-1 text-xs text-verify-fail">File is required</p>
            )}
          </div>
          <div>
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...form.register('name')} disabled={mutation.isPending} />
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" {...form.register('description')} disabled={mutation.isPending} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="version">Version</Label>
              <Input id="version" {...form.register('version')} disabled={mutation.isPending} />
            </div>
            <div>
              <Label htmlFor="framework">Framework</Label>
              <Input id="framework" {...form.register('framework')} disabled={mutation.isPending} />
            </div>
            <div>
              <Label htmlFor="framework_version">Framework version</Label>
              <Input
                id="framework_version"
                {...form.register('framework_version')}
                disabled={mutation.isPending}
              />
            </div>
            <div>
              <Label htmlFor="architecture">Architecture</Label>
              <Input
                id="architecture"
                {...form.register('architecture')}
                disabled={mutation.isPending}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400">Status:</span>
            {phase === 'idle' && <Badge variant="muted">Ready</Badge>}
            {phase === 'uploading' && <Badge variant="pending">Uploading…</Badge>}
            {phase === 'hashing' && <Badge variant="pending">Hashing on server…</Badge>}
            {phase === 'pending_tx' && <Badge variant="pending">Awaiting tx confirmation…</Badge>}
            {phase === 'success' && <Badge variant="ok">Confirmed</Badge>}
            {phase === 'error' && <Badge variant="fail">Failed</Badge>}
          </div>

          {error && <Alert variant="error">{error}</Alert>}
          {result && phase === 'success' && (
            <Alert variant="success">
              Registered {result.name}. Tx {result.transaction_hash.slice(0, 18)}… · block{' '}
              {result.block_number}
              <div className="mt-2">
                <Link
                  className="underline"
                  to={`/models/${encodeURIComponent(result.model_id)}`}
                >
                  View model details
                </Link>
              </div>
            </Alert>
          )}

          <Button type="submit" disabled={mutation.isPending || !file}>
            {mutation.isPending ? 'Registering…' : 'Register on blockchain'}
          </Button>
        </form>
        <CardDescription className="mt-4">
          Pending/failed transactions never appear as successful registrations.
        </CardDescription>
      </Card>
    </div>
  );
}
