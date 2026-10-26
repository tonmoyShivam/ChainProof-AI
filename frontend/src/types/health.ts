export type HealthResponse = {
  status: 'ok';
  service: string;
  environment: string;
};

export type BlockchainHealthResponse = {
  status: 'ok' | 'unavailable';
  connected: boolean;
  rpc_url: string;
  chain_id?: number | null;
  latest_block?: number | null;
  expected_chain_id?: number | null;
  detail: string;
};
