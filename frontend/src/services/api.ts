import type { BlockchainHealthResponse, HealthResponse } from '../types/health';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/api/v1/health');
}

export function fetchBlockchainHealth(): Promise<BlockchainHealthResponse> {
  return getJson<BlockchainHealthResponse>('/api/v1/health/blockchain');
}
