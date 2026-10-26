import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Fingerprint, Link2, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/services/api';

export function LandingPage() {
  const { isAuthenticated } = useAuth();
  const health = useQuery({ queryKey: ['health'], queryFn: api.health, retry: false });

  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      <div className="max-w-2xl">
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-accent-muted">
          AI model provenance
        </p>
        <h1 className="font-display text-4xl font-bold tracking-tight text-white sm:text-5xl">
          VerityAI
        </h1>
        <p className="mt-4 text-lg text-slate-300">
          Register AI model fingerprints on a local EVM, verify integrity with SHA-256, and
          inspect tamper-evident version history — without fabricated hashes or dashboard
          statistics.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          {isAuthenticated ? (
            <Link to="/dashboard">
              <Button>
                Open dashboard <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          ) : (
            <>
              <Link to="/register-account">
                <Button>
                  Create account <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline">Sign in</Button>
              </Link>
            </>
          )}
        </div>
        <div className="mt-4">
          {health.isLoading && <Badge variant="pending">Checking API…</Badge>}
          {health.isError && <Badge variant="fail">API unavailable</Badge>}
          {health.data && <Badge variant="ok">{health.data.service} online</Badge>}
        </div>
      </div>

      <section className="mt-16 grid gap-4 md:grid-cols-3">
        <Card>
          <Fingerprint className="h-5 w-5 text-accent-muted" />
          <CardTitle className="mt-3">Cryptographic fingerprints</CardTitle>
          <CardDescription>
            Server-side SHA-256 of uploaded artifacts — never trust a client-supplied hash.
          </CardDescription>
        </Card>
        <Card>
          <Link2 className="h-5 w-5 text-accent-muted" />
          <CardTitle className="mt-3">On-chain provenance</CardTitle>
          <CardDescription>
            ModelProvenance records identity, creator wallet, metadata digest, and version
            lineage on Hardhat.
          </CardDescription>
        </Card>
        <Card>
          <ShieldCheck className="h-5 w-5 text-accent-muted" />
          <CardTitle className="mt-3">Independent verification</CardTitle>
          <CardDescription>
            Re-hash a file and compare against the authoritative on-chain fingerprint.
          </CardDescription>
        </Card>
      </section>

      <section className="mt-16 border-t border-navy-700 pt-10">
        <h2 className="text-xl font-semibold text-white">How verification works</h2>
        <ol className="mt-4 space-y-3 text-sm text-slate-300">
          <li>1. Upload a model and register its fingerprint after blockchain confirmation.</li>
          <li>2. Later, upload the same (or altered) file with the model ID.</li>
          <li>
            3. VerityAI returns VERIFIED, INTEGRITY_MISMATCH, MODEL_NOT_FOUND, or UNAVAILABLE.
          </li>
        </ol>
        <p className="mt-6 text-sm text-slate-400">
          Stack: React · FastAPI · PostgreSQL/SQLite · Hardhat · Solidity 0.8
        </p>
      </section>
    </div>
  );
}
