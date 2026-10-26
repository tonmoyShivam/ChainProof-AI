/** Pure helpers for verification UI — unit-tested; no fabricated results. */

export type VerificationOutcome = 'match' | 'mismatch' | 'unavailable' | 'error';

export function classifyVerification(input: {
  match?: boolean | null;
  blockchainAvailable?: boolean | null;
  errorCode?: string | null;
}): VerificationOutcome {
  if (input.errorCode || input.match == null) {
    if (input.blockchainAvailable === false) return 'unavailable';
    return 'error';
  }
  if (input.blockchainAvailable === false) return 'unavailable';
  return input.match ? 'match' : 'mismatch';
}

export function verificationHeadline(outcome: VerificationOutcome): string {
  switch (outcome) {
    case 'match':
      return 'Integrity match';
    case 'mismatch':
      return 'Integrity mismatch';
    case 'unavailable':
      return 'Blockchain unavailable';
    default:
      return 'Verification could not complete';
  }
}
