import { useEffect, useState } from 'react';
import { fetchBlockchainHealth, fetchHealth } from '../services/api';
import type { BlockchainHealthResponse, HealthResponse } from '../types/health';

type LoadState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

const initialState = <T,>(): LoadState<T> => ({
  data: null,
  error: null,
  loading: true,
});

export function HomePage() {
  const [health, setHealth] = useState(initialState<HealthResponse>());
  const [chain, setChain] = useState(initialState<BlockchainHealthResponse>());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchHealth();
        if (!cancelled) setHealth({ data, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setHealth({
            data: null,
            error: err instanceof Error ? err.message : 'Health check failed',
            loading: false,
          });
        }
      }

      try {
        const data = await fetchBlockchainHealth();
        if (!cancelled) setChain({ data, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setChain({
            data: null,
            error: err instanceof Error ? err.message : 'Blockchain health check failed',
            loading: false,
          });
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-accent-muted">
        Milestone 1 · Project Foundation
      </p>
      <h1 className="font-display text-4xl font-bold tracking-tight text-white sm:text-5xl">
        VerityAI
      </h1>
      <p className="mt-4 max-w-xl text-lg text-slate-300">
        Blockchain-based AI model provenance and integrity verification. This
        foundation wires the React frontend, FastAPI backend, Hardhat local EVM,
        and PostgreSQL scaffolding.
      </p>

      <div className="mt-10 space-y-4 border-t border-navy-700 pt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Infrastructure status
        </h2>

        <StatusRow
          label="API"
          loading={health.loading}
          ok={health.data?.status === 'ok'}
          detail={
            health.error ??
            (health.data
              ? `${health.data.service} · ${health.data.environment}`
              : '—')
          }
        />
        <StatusRow
          label="Blockchain RPC"
          loading={chain.loading}
          ok={chain.data?.connected === true}
          detail={
            chain.error ??
            (chain.data
              ? `${chain.data.detail}${
                  chain.data.latest_block != null
                    ? ` · block ${chain.data.latest_block}`
                    : ''
                }`
              : '—')
          }
        />
      </div>
    </main>
  );
}

function StatusRow({
  label,
  loading,
  ok,
  detail,
}: {
  label: string;
  loading: boolean;
  ok: boolean;
  detail: string;
}) {
  let badge = 'Pending';
  let badgeClass = 'bg-verify-pending/15 text-verify-pending';

  if (!loading) {
    if (ok) {
      badge = 'OK';
      badgeClass = 'bg-verify-ok/15 text-verify-ok';
    } else {
      badge = 'Unavailable';
      badgeClass = 'bg-verify-fail/15 text-verify-fail';
    }
  }

  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className="font-medium text-slate-200">{label}</span>
        <span className={`rounded px-2 py-0.5 font-mono text-xs ${badgeClass}`}>
          {loading ? 'Checking…' : badge}
        </span>
      </div>
      <p className="font-mono text-sm text-slate-400">{detail}</p>
    </div>
  );
}
