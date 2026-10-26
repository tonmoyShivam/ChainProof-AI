import { describe, expect, it } from 'vitest';
import { classifyVerification, verificationHeadline } from './verification';
import { cn } from './cn';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-2', 'px-4')).toContain('px-4');
  });
});

describe('classifyVerification', () => {
  it('reports match when hashes agree and chain is up', () => {
    expect(
      classifyVerification({ match: true, blockchainAvailable: true }),
    ).toBe('match');
  });

  it('reports mismatch for altered artifacts', () => {
    expect(
      classifyVerification({ match: false, blockchainAvailable: true }),
    ).toBe('mismatch');
  });

  it('reports unavailable when RPC is down', () => {
    expect(
      classifyVerification({ match: null, blockchainAvailable: false }),
    ).toBe('unavailable');
  });
});

describe('verificationHeadline', () => {
  it('uses clear wording for success and failure', () => {
    expect(verificationHeadline('match')).toMatch(/match/i);
    expect(verificationHeadline('mismatch')).toMatch(/mismatch/i);
  });
});
