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

export type User = {
  id: string;
  email: string;
  display_name: string;
  wallet_address?: string | null;
  role: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: 'bearer';
};

export type ModelVersion = {
  id: string;
  on_chain_model_id: string;
  version_number: number;
  parent_version_id?: string | null;
  sha256_hash: string;
  metadata_hash: string;
  framework: string;
  framework_version: string;
  architecture: string;
  storage_path: string;
  storage_type: string;
  contract_address: string;
  chain_id: number;
  transaction_hash: string;
  block_number: number;
  registration_status: string;
  registered_at: string;
};

export type ModelDetail = {
  model_id: string;
  name: string;
  description: string;
  creator_user_id: string;
  creator_wallet: string;
  current_version: number;
  created_at: string;
  updated_at: string;
  latest_version?: ModelVersion | null;
};

export type ModelRegistration = {
  model_id: string;
  name: string;
  description: string;
  version_label: string;
  on_chain_version: number;
  parent_model_id?: string | null;
  sha256_hash: string;
  metadata_hash: string;
  storage_path: string;
  creator_user_id: string;
  creator_wallet: string;
  contract_address: string;
  chain_id: number;
  transaction_hash: string;
  block_number: number;
  registration_status: 'confirmed';
  framework: string;
  framework_version: string;
  architecture: string;
  created_at: string;
};

export type VerificationResult = {
  status: 'VERIFIED' | 'INTEGRITY_MISMATCH' | 'MODEL_NOT_FOUND' | 'VERIFICATION_UNAVAILABLE';
  model_id: string;
  expected_hash?: string | null;
  actual_hash?: string | null;
  detail: string;
  creator_wallet?: string | null;
  on_chain_version?: number | null;
};

export type VerificationLog = {
  id: string;
  model_version_id?: string | null;
  requested_model_id: string;
  provided_hash?: string | null;
  expected_hash?: string | null;
  result: string;
  error_code?: string | null;
  created_at: string;
};

export type DashboardStats = {
  total_registered_models: number;
  total_verification_attempts: number;
  successful_verifications: number;
  integrity_mismatches: number;
};

export type RecentActivityItem = {
  model_id: string;
  name: string;
  version: number;
  registration_time: string;
  creator: string;
  status: string;
  transaction_hash?: string | null;
};

export type ApiErrorBody = {
  error_code?: string;
  detail?: string | { msg?: string }[];
};
