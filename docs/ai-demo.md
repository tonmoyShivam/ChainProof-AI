# AI Demonstration Guide

See the runnable package at [`examples/ai-demo/README.md`](../examples/ai-demo/README.md).

## Scope

Milestone 7 adds a **demonstration** that VerityAI can:

1. Fingerprint a small model artifact (SHA-256)
2. Register it on the local EVM via the existing API
3. Verify before inference
4. Reject a one-byte-altered copy

This does **not** expand the product claim: hashes demonstrate integrity/provenance of bytes, not model accuracy or safety.

## Safe format choice

The demo uses a JSON weight file (`verityai-demo-linear-v1`) instead of pickle/joblib so loading does not require unsafe deserialization even when a hash matches.
